(() => {
  const cityCenter = [41.3168, 2.0201];
  const goarLocation = [41.3229755, 2.0066907];
  const leafletCss = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
  const leafletJs = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
  const scannerJs = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js';
  let cityMap;
  let shopMarkers;
  let scannerStream;
  let scannerFrame;
  let scannerVideo;
  let scannerCanvas;
  let scannerTarget;
  let scanning = false;

  const styleLink = document.createElement('link');
  styleLink.rel = 'stylesheet';
  styleLink.href = './viladecans.css';
  document.head.append(styleLink);

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`No se pudo cargar ${src}`));
      document.head.append(script);
    });
  }

  function loadStyle(src) {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = src;
      link.onload = resolve;
      link.onerror = () => reject(new Error(`No se pudo cargar ${src}`));
      document.head.append(link);
    });
  }

  function setProfile() {
    document.querySelector('.avatar').textContent = 'SG';
    document.querySelector('.user b').textContent = 'Sergi';
    document.querySelector('.user small').textContent = 'Goar · Viladecans';
    document.querySelector('.welcome h1').innerHTML = 'Bon dia, Sergi <span aria-hidden="true">✳</span>';
    document.querySelector('.school-name').textContent = 'Goar';
    document.querySelector('.mini-league b').textContent = 'Liga de institutos';
    document.querySelector('.mini-league p').textContent = 'Goar lidera la liga de Viladecans.';
    document.querySelector('#screen-league .personal h2').textContent = 'El Goar cuenta contigo.';
    document.querySelector('#screen-league .personal p').textContent = 'Tu constancia suma puntos al Goar y acerca el trofeo a todo el equipo.';
    document.querySelectorAll('#screen-league .rank-row')[0].querySelector('.school-row-name').innerHTML = 'Goar<small>Viladecans · Can Palmer</small>';
    document.querySelectorAll('#screen-league .rank-row')[0].classList.add('mine');
  }

  window.applyCitizenProfile = (name, school) => {
    const nameParts = name.trim().split(/\s+/);
    const initials = nameParts.length > 1 ? `${nameParts[0][0]}${nameParts.at(-1)[0]}` : `${name[0]}${school[0]}`;
    document.querySelector('.avatar').textContent = initials.toUpperCase();
    document.querySelector('.user b').textContent = name;
    document.querySelector('.user small').textContent = `${school} · Viladecans`;
    const heading = document.querySelector('.welcome h1');
    const sparkle = heading.querySelector('span');
    heading.textContent = `Bon dia, ${name} `;
    heading.append(sparkle);
    document.querySelector('.school-name').textContent = school;
    document.querySelector('.mini-league p').textContent = `${school} suma en la liga de Viladecans.`;
    document.querySelector('#screen-league .personal h2').textContent = `El ${school} cuenta contigo.`;
    document.querySelector('#screen-league .personal p').textContent = `Tu constancia suma puntos al ${school} y acerca el trofeo a todo el equipo.`;
    const schoolRow = document.querySelector('#screen-league .rank-row .school-row-name');
    schoolRow.textContent = school;
    const schoolLocation = document.createElement('small');
    schoolLocation.textContent = 'Viladecans';
    schoolRow.append(schoolLocation);
  };

  window.setCitizenDashboard = dashboard => {
    state.balance = dashboard.balance;
    state.contribution = dashboard.contribution;
    update();
    const stepCard = document.querySelector('.steps');
    stepCard.querySelector('strong').textContent = `${dashboard.steps.count.toLocaleString('es-ES')} pasos`;
    stepCard.querySelector('span').textContent = `de ${dashboard.steps.goal.toLocaleString('es-ES')}`;
    stepCard.parentElement.querySelector('.progress span').style.width = `${Math.min(100, dashboard.steps.count / dashboard.steps.goal * 100)}%`;
    stepCard.parentElement.querySelector('.points').textContent = 'PENDIENTE';
    stepCard.parentElement.querySelector('p').textContent = 'Sincronización con una fuente de pasos pendiente.';
    document.querySelector('#route-status').textContent = 'Los puntos de EcoRuta se mostrarán al conectarse el servicio municipal.';
    document.querySelector('.balance .trend').textContent = 'SALDO DE DEMOSTRACIÓN';
    document.querySelector('.habit:nth-child(2) h3').textContent = 'Compras verificadas';
    document.querySelector('.habit:nth-child(2) p').textContent = 'Aún no hay compras confirmadas por un comercio.';
    document.querySelector('.school-note').textContent = 'Puntos acumulados en los perfiles registrados en esta demo.';
    document.querySelectorAll('.panel .activity').forEach(activity => activity.remove());
    document.querySelector('#activity-empty')?.remove();
    if (dashboard.activity.length) {
      dashboard.activity.forEach(item => {
        const row = document.createElement('div');
        row.className = 'activity';
        const icon = document.createElement('span');
        icon.className = 'activity-icon';
        icon.innerHTML = '<i data-lucide="scan-line"></i>';
        const copy = document.createElement('span');
        copy.className = 'activity-copy';
        const title = document.createElement('strong');
        title.textContent = item.description;
        const detail = document.createElement('small');
        detail.textContent = `${item.merchant} · ${new Intl.DateTimeFormat('es-ES', { hour: '2-digit', minute: '2-digit' }).format(new Date(item.created_at))}`;
        copy.append(title, detail);
        const points = document.createElement('span');
        points.className = 'activity-points';
        points.textContent = `+${item.points} pts`;
        row.append(icon, copy, points);
        document.querySelector('.panel').append(row);
      });
      icons();
    } else {
      document.querySelector('.panel').insertAdjacentHTML('beforeend', '<p class="empty" id="activity-empty">La actividad aparecerá aquí cuando se conecten las fuentes municipales.</p>');
    }
    const rows = document.querySelector('#screen-league .rank-table');
    rows.querySelectorAll('.rank-row').forEach(row => row.remove());
    dashboard.league.forEach((school, index) => {
      const row = document.createElement('div');
      row.className = `rank-row${school.school === document.querySelector('.school-name').textContent ? ' mine' : ''}`;
      const position = document.createElement('span');
      position.className = `rank-num${index === 0 ? ' gold' : ''}`;
      position.textContent = String(index + 1).padStart(2, '0');
      const name = document.createElement('span');
      name.className = 'school-row-name';
      name.textContent = school.school;
      const score = document.createElement('span');
      score.className = 'school-score';
      score.textContent = school.points.toLocaleString('es-ES');
      const delta = document.createElement('span');
      delta.className = 'delta';
      delta.textContent = '—';
      row.append(position, name, score, delta);
      rows.append(row);
    });
    document.querySelector('#screen-home .rank-pill').textContent = `#${dashboard.school_rank} DE ${dashboard.league.length}`;
    document.querySelector('#screen-home .school-stats span:last-child b').textContent = `#${dashboard.personal_rank}`;
    document.querySelector('#screen-league .personal .metrics > div:last-child strong').textContent = `#${dashboard.personal_rank}`;
    save();
  };

  window.setCitizenWallet = (rewardItems, activeCoupons, redeemedCoupons) => {
    prizes.splice(0, prizes.length, ...rewardItems);
    state.coupons = activeCoupons;
    state.redeemedCoupons = redeemedCoupons;
    save();
    update();
    renderWallet();
    document.querySelectorAll('#rewards .reward').forEach((card, index) => {
      if (!prizes[index]?.is_demo) return;
      const tag = document.createElement('span');
      tag.className = 'demo-tag';
      tag.textContent = 'Oferta de demostración';
      card.querySelector('.merchant-tag').after(tag);
    });
  };

  window.setCitizenMerchants = entries => {
    shops.splice(0, shops.length, ...entries);
    renderShopList();
  };

  window.setCitizenLocalDemo = () => {
    shops.forEach(shop => {
      shop.is_demo = true;
      shop.latitude = null;
      shop.longitude = null;
      shop.distance = null;
    });
    prizes.forEach(prize => { prize.is_demo = true; });
    renderShopList();
    renderWallet();
  };

  window.setCitizenLocation = (latitude, longitude) => {
    for (const shop of shops) {
      if (shop.latitude == null || shop.longitude == null) continue;
      const radians = Math.PI / 180;
      const deltaLatitude = (shop.latitude - latitude) * radians;
      const deltaLongitude = (shop.longitude - longitude) * radians;
      const arc = Math.sin(deltaLatitude / 2) ** 2 + Math.cos(latitude * radians) * Math.cos(shop.latitude * radians) * Math.sin(deltaLongitude / 2) ** 2;
      shop.distance = `${Math.round(6371000 * 2 * Math.atan2(Math.sqrt(arc), Math.sqrt(1 - arc)) / 50) * 50} m`;
    }
    shops.sort((first, second) => {
      if (first.latitude == null) return 1;
      if (second.latitude == null) return -1;
      return parseInt(first.distance, 10) - parseInt(second.distance, 10);
    });
    cityMap?.setView([latitude, longitude], 15);
    renderShopList();
  };

  const locations = [
    [41.3174, 2.0202],
    [41.3165, 2.0221],
    [41.3185, 2.0184],
    [41.3148, 2.0163],
    [41.3202, 2.0228],
    [41.3129, 2.0198]
  ];

  function renderShopPins() {
    if (!cityMap || !shopMarkers) return;
    shopMarkers.clearLayers();
    shops.filter(shop => shop.latitude != null && shop.longitude != null && (category === 'Todos' || shop.category === category)).forEach(shop => {
      const marker = L.marker([shop.latitude, shop.longitude]).bindPopup(`<strong>${shop.name}</strong><br>${shop.address}`);
      marker.on('click', () => chooseShop(shop.name));
      marker.addTo(shopMarkers);
    });
  }

  function renderShopList() {
    const visible = shops.filter(shop => category === 'Todos' || shop.category === category);
    document.querySelector('#filters').innerHTML = categories.map(item => `<button class="chip ${item === category ? 'active' : ''}" data-category="${item}">${item}</button>`).join('');
    document.querySelector('#merchant-list').innerHTML = visible.map(shop => `<button class="merchant ${chosen?.name === shop.name ? 'selected' : ''}" data-shop="${shop.name}"><span class="merchant-logo">${shop.initials}</span><span class="merchant-info"><strong>${shop.name}</strong><small>${shop.is_demo ? 'Ejemplo · no confirmado' : `${shop.type} · ${shop.address}`}</small></span><span class="distance">${shop.distance || '—'}</span></button>`).join('');
    renderShopPins();
  }

  function initializeMap() {
    const mapElement = document.querySelector('#map');
    mapElement.replaceChildren();
    cityMap = L.map(mapElement, { scrollWheelZoom: false }).setView(cityCenter, 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(cityMap);
    shopMarkers = L.layerGroup().addTo(cityMap);
    L.marker(goarLocation).bindPopup('<strong>Goar</strong><br>Carrer de la Circumval·lació, Viladecans').addTo(cityMap);
    renderShopPins();
  }

  function ensureCouponHistory() {
    if (!Array.isArray(state.redeemedCoupons)) state.redeemedCoupons = [];
    if (!Array.isArray(state.coupons)) state.coupons = [];
    state.coupons.forEach(coupon => {
      if (!coupon.code) coupon.code = `VC-${crypto.randomUUID().slice(0, 5).toUpperCase()}`;
    });
    save();
  }

  function couponPayload(code) {
    return `VILACIRCULA|${code}`;
  }

  function fillQr(element, value, size) {
    element.replaceChildren();
    if (window.QRCode) {
      new QRCode(element, {
        text: value,
        width: size,
        height: size,
        colorDark: '#19281f',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.M
      });
    } else {
      element.textContent = value;
      element.classList.add('qr-unavailable');
    }
  }

  function renderWallet() {
    document.querySelector('#rewards').innerHTML = prizes.map(prize => `<article class="reward"><div class="reward-art ${prize.art}"><i data-lucide="${prize.icon}"></i></div><div class="reward-info"><span class="merchant-tag">${prize.store}</span><h3>${prize.name}</h3><p>${prize.description}</p><div class="reward-foot"><span class="cost">${prize.cost} ECO PTS</span><button class="redeem" data-redeem="${prize.id}" ${state.balance < prize.cost ? 'disabled' : ''}>Canjear</button></div></div></article>`).join('');
    const count = document.querySelector('#coupon-count');
    count.textContent = `${state.coupons.length} VALES`;
    count.parentElement.classList.add('coupon-heading');
    let scanButton = document.querySelector('#scan-coupon');
    if (!scanButton) {
      scanButton = document.createElement('button');
      scanButton.id = 'scan-coupon';
      scanButton.className = 'scan-coupon';
      scanButton.innerHTML = '<i data-lucide="scan-qr-code"></i>Escanear cupón';
      count.parentElement.append(scanButton);
    }
    document.querySelector('#coupons').innerHTML = state.coupons.length
      ? state.coupons.map(coupon => `<article class="coupon"><button class="coupon-qr" data-open-coupon="${coupon.code}" aria-label="Ver QR de ${coupon.name}"><span id="coupon-qr-${coupon.code}"></span></button><span class="coupon-text"><b>${coupon.name}</b><small>${coupon.store} · Válido hasta ${coupon.expiry}</small><button class="coupon-view" data-open-coupon="${coupon.code}">Ver QR y canjear</button></span><span class="coupon-code">${coupon.code}</span></article>`).join('')
      : '<p class="empty">Tus próximos premios aparecerán aquí.</p>';
    document.querySelectorAll('[id^="coupon-qr-"]').forEach(qr => {
      const code = qr.id.replace('coupon-qr-', '');
      fillQr(qr, couponPayload(code), 68);
    });
    const history = document.querySelector('#redeemed-coupons');
    if (history) history.remove();
    if (state.redeemedCoupons.length) {
      const section = document.createElement('section');
      section.id = 'redeemed-coupons';
      section.className = 'redeemed-list';
      section.innerHTML = `<h3>Cupones canjeados <span>${state.redeemedCoupons.length}</span></h3>${state.redeemedCoupons.map(coupon => `<div class="redeemed-row"><i data-lucide="circle-check"></i><span><b>${coupon.name}</b><small>${coupon.store} · Canjeado ${coupon.redeemedAt || 'hoy'}</small></span><strong>CANJEADO</strong></div>`).join('')}`;
      document.querySelector('.coupon-list').append(section);
    }
    icons();
  }

  function redeemReward(id) {
    const prize = prizes.find(item => item.id === id);
    if (!prize || state.balance < prize.cost) return toast('Te faltan EcoPuntos para este vale.');
    state.balance -= prize.cost;
    state.coupons.unshift({
      name: prize.name,
      store: prize.store,
      code: `VC-${crypto.randomUUID().replaceAll('-', '').slice(0, 5).toUpperCase()}`,
      expiry: '31 oct'
    });
    save();
    update();
    renderWallet();
    toast(`Vale guardado: ${prize.name}`);
  }

  function closeCouponModal() {
    scanning = false;
    if (scannerFrame) cancelAnimationFrame(scannerFrame);
    scannerFrame = null;
    scannerStream?.getTracks().forEach(track => track.stop());
    scannerStream = null;
    document.querySelector('#coupon-modal')?.remove();
  }

  window.closeCitizenCouponModal = closeCouponModal;

  function markRedeemed(code) {
    if (window.apiCouponRedeem) return window.apiCouponRedeem(code);
    const index = state.coupons.findIndex(coupon => coupon.code === code);
    if (index < 0) {
      toast('Este QR no corresponde a un cupón activo.');
      return false;
    }
    const [coupon] = state.coupons.splice(index, 1);
    state.redeemedCoupons.unshift({ ...coupon, redeemedAt: new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short' }).format(new Date()) });
    save();
    closeCouponModal();
    renderWallet();
    toast(`Cupón canjeado: ${coupon.name}`);
    if ('vibrate' in navigator) navigator.vibrate([70, 35, 70]);
    return true;
  }

  function couponCodeFrom(rawValue) {
    return rawValue.match(/VC-[A-Z0-9]{5,12}/i)?.[0]?.toUpperCase() || null;
  }

  async function startCameraScan() {
    const status = document.querySelector('#scanner-status');
    const video = document.querySelector('#coupon-video');
    const preview = document.querySelector('#scanner-preview');
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('Este navegador no permite usar la cámara.');
      scannerStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
      scannerVideo = video;
      scannerCanvas = document.createElement('canvas');
      video.srcObject = scannerStream;
      await video.play();
      preview.hidden = false;
      status.textContent = 'Apunta al QR de un cupón VilaCircula.';
      scanning = true;
      let detector;
      if ('BarcodeDetector' in window) detector = new BarcodeDetector({ formats: ['qr_code'] });
      else if (!window.jsQR) await loadScript(scannerJs);
      const scanFrame = async () => {
        if (!scanning) return;
        try {
          let decoded;
          if (detector) {
            const codes = await detector.detect(video);
            decoded = codes[0]?.rawValue;
          } else if (video.readyState === HTMLMediaElement.HAVE_ENOUGH_DATA) {
            scannerCanvas.width = video.videoWidth;
            scannerCanvas.height = video.videoHeight;
            const context = scannerCanvas.getContext('2d', { willReadFrequently: true });
            context.drawImage(video, 0, 0, scannerCanvas.width, scannerCanvas.height);
            decoded = window.jsQR(context.getImageData(0, 0, scannerCanvas.width, scannerCanvas.height).data, scannerCanvas.width, scannerCanvas.height)?.data;
          }
          if (decoded) {
            const code = couponCodeFrom(decoded);
            if (code && await markRedeemed(code)) return;
            if (!code) status.textContent = 'Ese QR no es un cupón VilaCircula. Sigue enfocando el QR del vale.';
          }
        } catch (error) {
          status.textContent = error.message || 'No pudimos leer el QR. Ajusta el enfoque e inténtalo de nuevo.';
        }
        scannerFrame = requestAnimationFrame(scanFrame);
      };
      scanFrame();
    } catch (error) {
      status.textContent = error.message.includes('Permission') || error.name === 'NotAllowedError'
        ? 'Permite el acceso a la cámara para escanear el cupón.'
        : error.message;
    }
  }

  function openCoupon(code = null) {
    const coupon = code ? state.coupons.find(item => item.code === code) : null;
    const modal = document.createElement('div');
    modal.id = 'coupon-modal';
    modal.className = 'modal-backdrop';
    modal.innerHTML = `<section class="modal coupon-modal" role="dialog" aria-modal="true" aria-labelledby="coupon-modal-title"><button class="icon-button modal-close" id="close-coupon" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">MONEDERO VILACIRCULA</span><h2 id="coupon-modal-title">${coupon ? coupon.name : 'Escanea un cupón'}</h2><p>${coupon ? `${coupon.store} · Código de un solo uso` : 'Lee el QR de un cupón activo para marcarlo como canjeado.'}</p>${coupon ? `<div class="coupon-large-qr" id="coupon-large-qr"></div><div class="coupon-large-code">${coupon.code}</div>` : ''}<div class="scanner-preview" id="scanner-preview" hidden><video id="coupon-video" playsinline muted></video><span class="scan-frame"></span></div><p class="scanner-status" id="scanner-status">${coupon ? 'Muestra este QR al comercio o escanea aquí un vale activo.' : 'La cámara solo se usa para leer el QR de un cupón.'}</p><div class="coupon-modal-actions"><button class="primary" id="start-coupon-scan"><i data-lucide="scan-line"></i>Escanear con cámara</button>${coupon ? '<button class="redeem" id="simulate-coupon-scan">Simular escaneo</button>' : ''}</div></section>`;
    document.querySelector('#modal-root').append(modal);
    icons();
    if (coupon) fillQr(document.querySelector('#coupon-large-qr'), couponPayload(coupon.code), 202);
    modal.addEventListener('click', event => { if (event.target === modal) closeCouponModal(); });
    document.querySelector('#close-coupon').addEventListener('click', closeCouponModal);
    document.querySelector('#start-coupon-scan').addEventListener('click', startCameraScan);
    document.querySelector('#simulate-coupon-scan')?.addEventListener('click', () => markRedeemed(coupon.code));
  }

  function installEnhancements() {
    setProfile();
    ensureCouponHistory();
    window.drawShops = renderShopList;
    window.drawWallet = renderWallet;
    window.redeem = redeemReward;
    renderShopList();
    renderWallet();

    document.addEventListener('click', event => {
      const walletButton = event.target.closest('#scan-coupon');
      if (walletButton) return openCoupon();
      const couponButton = event.target.closest('[data-open-coupon]');
      if (couponButton) return openCoupon(couponButton.dataset.openCoupon);
      if (event.target.closest('[data-screen="shops"]')) setTimeout(() => cityMap?.invalidateSize(), 100);
    });
  }

  Promise.all([loadStyle(leafletCss), loadScript(leafletJs)])
    .then(initializeMap)
    .catch(() => {
      document.querySelector('#map').innerHTML = '<div class="map-error">No se pudo cargar el mapa. Comprueba la conexión para ver las calles de Viladecans.</div>';
    });

  installEnhancements();
})();
