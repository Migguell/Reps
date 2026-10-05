const isLocalhost = typeof window !== 'undefined' && (
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1' ||
  window.location.hostname === '0.0.0.0'
);

const envApiUrl = (typeof window !== 'undefined' && window.__ENV__ && window.__ENV__.API_URL)
  ? window.__ENV__.API_URL
  : 'https://api.reps-fitness.com';

const API_BASE = isLocalhost ? 'http://localhost:5000' : envApiUrl;


class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.state = {
      now: Date.now(),
      mx: 0.5,
      my: 0.3,
      hover: false,
      priceFive: '---',
      priceFivePerClass: '---',
      priceTen: '---',
      priceTenPerClass: '---',
      loadingBundle: null,
      statusNotice: null,
      statusNoticeText: '',
      sendingEmail: false
    };
    this.onMove = this.onMove.bind(this);
    this.onLeave = this.onLeave.bind(this);
    this.handleBuy = this.handleBuy.bind(this);
    this.handleSubmitLead = this.handleSubmitLead.bind(this);
    this.lastMove = 0;
  }

  onMove(e) {
    const now = Date.now();
    if (now - this.lastMove < 40) return;
    this.lastMove = now;

    const rect = e.currentTarget.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    const touch = e.touches && e.touches[0];
    const clientX = touch ? touch.clientX : e.clientX;
    const clientY = touch ? touch.clientY : e.clientY;

    if (clientX === undefined || clientY === undefined) return;

    const x = (clientX - rect.left) / rect.width;
    const y = (clientY - rect.top) / rect.height;

    this.setState({
      mx: Math.max(0, Math.min(1, x)),
      my: Math.max(0, Math.min(1, y)),
      hover: true
    });
  }

  onLeave() {
    this.setState({ mx: 0.5, my: 0.3, hover: false });
  }

  componentDidMount() {
    this.timer = setInterval(() => {
      this.setState({ now: Date.now() });
    }, 1000);

    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('status') === 'success') {
        this.setState({ statusNotice: 'success' });
      } else if (params.get('status') === 'cancelled') {
        this.setState({ statusNotice: 'cancelled' });
      }
    }

    this.fetchPrices();
  }

  componentWillUnmount() {
    if (this.timer) {
      clearInterval(this.timer);
    }
  }

  handleSubmitLead(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (this.state.sendingEmail) return;

    const input = document.getElementById('email');
    const email = input ? input.value.trim() : '';

    if (!email) {
      this.setState({
        statusNotice: 'email_error',
        statusNoticeText: 'Please enter your email address.'
      });
      return;
    }

    this.setState({ sendingEmail: true });

    fetch(`${API_BASE}/api/send-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    })
      .then(res => res.json())
      .then(json => {
        if (json.data) {
          if (input) input.value = '';
          this.setState({
            sendingEmail: false,
            statusNotice: 'email_success',
            statusNoticeText: '✓ EMAIL SENT SUCCESSFULLY — CHECK YOUR INBOX.'
          });
        } else {
          throw new Error(json.error || 'Failed to send email.');
        }
      })
      .catch(err => {
        this.setState({
          sendingEmail: false,
          statusNotice: 'email_error',
          statusNoticeText: err.message || 'Unable to connect to the server.'
        });
      });
  }

  fetchPrices() {
    fetch(`${API_BASE}/api/prices`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to retrieve prices.');
        return res.json();
      })
      .then(json => {
        const data = json.data;
        if (data && data.five && data.ten) {
          this.setState({
            priceFive: data.five.formatted,
            priceFivePerClass: data.five.perClassFormatted,
            priceTen: data.ten.formatted,
            priceTenPerClass: data.ten.perClassFormatted
          });
        }
      })
      .catch(err => {
        console.warn('Unable to load prices from API:', err.message);
      });
  }

  handleBuy(bundle) {
    if (this.state.loadingBundle) return;
    this.setState({ loadingBundle: bundle });

    fetch(`${API_BASE}/api/create-checkout-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bundle })
    })
      .then(res => res.json())
      .then(json => {
        if (json.data && json.data.url) {
          window.location.href = json.data.url;
        } else {
          throw new Error(json.error || 'Checkout URL not returned by server.');
        }
      })
      .catch(err => {
        alert('Unable to start checkout: ' + err.message);
        this.setState({ loadingBundle: null });
      });
  }

  rgba(hex = '#396AFE', a = 1) {
    let h = String(hex).replace('#', '');
    if (h.length === 3) {
      h = h.split('').map(char => char + char).join('');
    }
    const r = parseInt(h.slice(0, 2), 16) || 0;
    const g = parseInt(h.slice(2, 4), 16) || 0;
    const b = parseInt(h.slice(4, 6), 16) || 0;
    return `rgba(${r}, ${g}, ${b}, ${a})`;
  }

  beam(hex) {
    return `linear-gradient(to bottom, ${this.rgba(hex, 0.7)} 0%, ${this.rgba(hex, 0.34)} 34%, ${this.rgba(hex, 0.12)} 62%, rgba(8, 7, 16, 0) 88%)`;
  }

  renderVals() {
    const {
      accent = '#FF3A46',
      lightBlue: blue = '#396AFE',
      lightMagenta: magenta = '#C62BC6',
      lightPurple: purple = '#8B3BFF',
      lightRed: red = '#FF3A46'
    } = this.props || {};

    const target = Date.parse('2026-12-15T18:00:00+03:00');
    const remaining = Math.max(0, target - this.state.now);
    const totalSeconds = Math.floor(remaining / 1000);

    const pad = (num, length = 2) => String(num).padStart(length, '0');

    const mx = typeof this.state.mx === 'number' ? this.state.mx : 0.5;
    const my = typeof this.state.my === 'number' ? this.state.my : 0.3;

    return {
      onMove: this.onMove,
      onLeave: this.onLeave,
      rigTilt: `${((mx - 0.5) * 8).toFixed(2)}deg`,
      parA: `${((mx - 0.5) * -70).toFixed(1)}px`,
      parB: `${((mx - 0.5) * 48).toFixed(1)}px`,
      parC: `${((mx - 0.5) * -26).toFixed(1)}px`,
      spotLeft: `${(mx * 100).toFixed(2)}%`,
      spotTop: `${(my * 100).toFixed(2)}%`,
      spotOn: this.state.hover ? '1' : '0',
      spotCore: this.rgba(magenta, 0.22),
      accent,
      accentLine: this.rgba(accent, 0.45),
      accentWash: this.rgba(accent, 0.12),
      lightBlue: blue,
      lightMagenta: magenta,
      lightPurple: purple,
      lightRed: red,
      beamBlue: this.beam(blue),
      beamMagenta: this.beam(magenta),
      beamPurple: this.beam(purple),
      beamRed: this.beam(red),
      glowPurple: this.rgba(purple, 0.22),
      blueLine: this.rgba(blue, 0.38),
      blueWash: this.rgba(blue, 0.1),
      purpleLine: this.rgba(purple, 0.38),
      purpleWash: this.rgba(purple, 0.1),
      magentaLine: this.rgba(magenta, 0.38),
      magentaWash: this.rgba(magenta, 0.1),
      glowBlue: this.rgba(blue, 0.28),
      glowMagenta: this.rgba(magenta, 0.26),
      days: pad(Math.floor(totalSeconds / 86400), 3),
      hours: pad(Math.floor((totalSeconds % 86400) / 3600), 2),
      mins: pad(Math.floor((totalSeconds % 3600) / 60), 2),
      secs: pad(totalSeconds % 60, 2),
      onBuyFive: () => this.handleBuy('five'),
      onBuyTen: () => this.handleBuy('ten'),
      onSubmitLead: this.handleSubmitLead,
      sendButtonText: this.state.sendingEmail ? 'SENDING...' : 'SEND',
      emailBtnClass: this.state.sendingEmail ? 'email-btn-loading' : '',
      buyFiveText: this.state.loadingBundle === 'five' ? 'REDIRECTING...' : 'BUY FIVE',
      buyTenText: this.state.loadingBundle === 'ten' ? 'REDIRECTING...' : 'BUY TEN',
      priceFive: this.state.priceFive,
      priceFivePerClass: this.state.priceFivePerClass,
      priceTen: this.state.priceTen,
      priceTenPerClass: this.state.priceTenPerClass,
      statusNoticeDisplay: this.state.statusNotice ? 'flex' : 'none',
      statusNoticeText: this.state.statusNotice === 'success'
        ? '✓ RESERVATION CONFIRMED — WELCOME TO THE REPS FOUNDING CLASS.'
        : this.state.statusNotice === 'cancelled'
        ? 'Checkout was not completed. You can select your bundle whenever you are ready.'
        : this.state.statusNoticeText || '',
      statusNoticeColor: (this.state.statusNotice === 'success' || this.state.statusNotice === 'email_success') ? '#2ECC71' : '#F39C12',
      onDismissNotice: () => this.setState({ statusNotice: null, statusNoticeText: '' })
    };
  }
}
