(() => {
  const LANGUAGE_KEY = 'vilacircula-language';
  const translations = {
    'Navegación principal': 'Navegació principal',
    'Navegación móvil': 'Navegació mòbil',
    'VilaCircula · Projecte Talent a les Aules': 'VilaCircula · Projecte Talent a les Aules',
    'Projecte Talent a les Aules': 'Projecte Talent a les Aules',
    'TU ESPACIO': 'EL TEU ESPAI',
    'Inicio': 'Inici',
    'Comercios': 'Comerços',
    'Liga local': 'Lliga local',
    'Liga': 'Lliga',
    'Recompensas': 'Recompenses',
    'Wallet': 'Moneder',
    'Liga de institutos': 'Lliga d’instituts',
    'Insti Sales lidera esta semana.': 'L’institut Sales lidera aquesta setmana.',
    'Abrir usuario y cuenta': 'Obrir usuari i compte',
    'Notificaciones': 'Notificacions',
    'Cada pequeño gesto hace una ciudad mejor.': 'Cada petit gest fa una ciutat millor.',
    'TU SALDO ECO': 'EL TEU SALDO ECO',
    'esta semana': 'aquesta setmana',
    '↗ +35 esta semana': '↗ +35 aquesta setmana',
    'EcoPuntos': 'EcoPunts',
    'EcoPuntos aportados': 'EcoPunts aportats',
    'Compras ECO verificadas': 'Compres ECO verificades',
    'Pasos registrados': 'Passos registrats',
    'kg CO₂ evitados': 'kg CO₂ evitats',
    'CO₂ evitado': 'CO₂ evitat',
    'compra ECO': 'compra ECO',
    'Puntos aportados': 'Punts aportats',
    'Ver movimientos ↗': 'Veure moviments ↗',
    'LISTA PARA SUMAR': 'A PUNT PER SUMAR',
    'Tu EcoID, en un toque.': 'El teu EcoID, a un toc.',
    'Enséñalo en tu comercio de confianza.': 'Ensenya’l al teu comerç de confiança.',
    'Mostrar mi EcoID': 'Mostra el meu EcoID',
    'Tu día más sostenible': 'El teu dia més sostenible',
    'HOY,': 'AVUI,',
    '1 / día': '1 / dia',
    'Hoy': 'Avui',
    'Ayer': 'Ahir',
    'de': 'de',
    'pasos': 'passos',
    'al alcanzar meta': 'en assolir l’objectiu',
    'conseguidos': 'aconseguits',
    'Estimación con el acelerómetro mientras la app está abierta.': 'Estimació amb l’acceleròmetre mentre l’aplicació està oberta.',
    'Activar contador de pasos': 'Activa el comptador de passos',
    'Pausar contador': 'Posa en pausa el comptador',
    'Compra consciente': 'Compra conscient',
    '+30 pts al alcanzar meta': '+30 punts en assolir l’objectiu',
    'Frutos secos · La Botiga Verda': 'Fruits secs · La Botiga Verda',
    'Hoy, 09:12': 'Avui, 09:12',
    'Camino al instituto · Ayer': 'Camí a l’institut · Ahir',
    'Parc de la Marina · Mar, 23 sept': 'Parc de la Marina · dt., 23 set.',
    'EcoRuta de hoy': 'EcoRuta d’avui',
    'Aún no has escaneado el punto de hoy.': 'Encara no has escanejat el punt d’avui.',
    'Tu actividad reciente': 'La teva activitat recent',
    'ESTA SEMANA': 'AQUESTA SETMANA',
    'Compra con bolsa propia': 'Compra amb bossa pròpia',
    'Hoy,': 'Avui,',
    'Movilidad activa': 'Mobilitat activa',
    'Camino al instituto': 'Camí a l’institut',
    'Ayer': 'Ahir',
    'EcoRuta del parc': 'EcoRuta del parc',
    'Parc de la Marina': 'Parc de la Marina',
    'CENTRE': 'CENTRE',
    'TORRE-ROJA': 'TORRE-ROJA',
    'Insti Sales · 3.º ESO': 'Institut Sales · 3r d’ESO',
    'Líderes de Viladecans esta semana': 'Líders de Viladecans aquesta setmana',
    'Pequeños gestos, grandes premios.': 'Petits gestos, grans premis.',
    'Final de liga · 6 de noviembre': 'Final de lliga · 6 de novembre',
    'VILADECANS · PERFIL CIUDADANO': 'VILADECANS · PERFIL CIUTADÀ',
    'JUEVES, 25 DE SEPTIEMBRE': 'DIJOUS, 25 DE SETEMBRE',
    'Cerca a prop meu': 'Cerca a prop meu',
    'Tu insti en la liga': 'El teu institut a la lliga',
    'Líderes de Viladecans esta semana': 'Líders de Viladecans aquesta setmana',
    'Tu aportación': 'La teva aportació',
    'Tu puesto': 'La teva posició',
    'CERCA DE TI · VILADECANS': 'A PROP TEU · VILADECANS',
    'Comercios con impacto.': 'Comerços amb impacte.',
    'Encuentra dónde ganar y gastar EcoPuntos.': 'Troba on guanyar i bescanviar EcoPunts.',
    'Buscar cerca de mí': 'Cerca a prop meu',
    'Abrir usuario, credenciales y caja': 'Obrir usuari, credencials i caixa',
    'Alimentación · Zero waste': 'Alimentació · residu zero',
    'Comercio local': 'Comerç local',
    'Ubicación no disponible': 'Ubicació no disponible',
    'Papelería · Material escolar': 'Papereria · material escolar',
    'Cafetería · Café de especialidad': 'Cafeteria · cafè d’especialitat',
    'Moda · Segunda mano': 'Moda · segona mà',
    'Panadería · Artesana': 'Forn · artesà',
    'Librería · Cultural': 'Llibreria · cultural',
    'Cafetería · comercio local': 'Cafeteria · comerç local',
    'Panadería y café · comercio local': 'Forn i cafè · comerç local',
    'Papelería · ficha ilustrativa': 'Papereria · fitxa il·lustrativa',
    'Moda · ficha ilustrativa': 'Moda · fitxa il·lustrativa',
    'Comercio de alimentación · ejemplo': 'Comerç d’alimentació · exemple',
    'Ficha y ubicación proceden de OpenStreetMap; confirma las condiciones con el local.': 'La fitxa i la ubicació provenen d’OpenStreetMap; confirma les condicions al comerç.',
    'Sin recompensas verificadas todavía.': 'Encara no hi ha recompenses verificades.',
    'Ficha ilustrativa; no representa un comercio adherido confirmado.': 'Fitxa il·lustrativa; no representa un comerç adherit confirmat.',
    'Los descuentos de esta ficha son de demostración.': 'Els descomptes d’aquesta fitxa són de demostració.',
    'Descuento ilustrativo; consulta condiciones en el local.': 'Descompte il·lustratiu; consulta les condicions al comerç.',
    'Premio ilustrativo; consulta condiciones en el local.': 'Premi il·lustratiu; consulta les condicions al comerç.',
    'Recompensa y comercio de demostración.': 'Recompensa i comerç de demostració.',
    'Recompensa de demostración.': 'Recompensa de demostració.',
    'Meta diaria de pasos alcanzada': 'Objectiu diari de passos assolit',
    'Escaneo de caja simulado': 'Escaneig de caixa simulat',
    'EcoID validado en caja': 'EcoID validat a caixa',
    'Ten VilaCircula en tu dispositivo.': 'Porta VilaCircula al teu dispositiu.',
    'Añádela al escritorio o a la pantalla de inicio para abrirla como una aplicación.': 'Afegeix-la a l’escriptori o a la pantalla d’inici per obrir-la com una aplicació.',
    'Añadir aplicación': 'Afegir aplicació',
    'Aplicación instalada': 'Aplicació instal·lada',
    'VilaCircula ya está instalada en este dispositivo.': 'VilaCircula ja està instal·lada en aquest dispositiu.',
    'VilaCircula se está añadiendo a este dispositivo.': 'S’està afegint VilaCircula a aquest dispositiu.',
    'Puedes instalarla más tarde desde el menú del navegador.': 'La pots instal·lar més tard des del menú del navegador.',
    'Abre VilaCircula en Safari.': 'Obre VilaCircula a Safari.',
    'Pulsa el botón Compartir.': 'Prem el botó Compartir.',
    'Elige «Añadir a pantalla de inicio» y confirma con «Añadir».': 'Tria «Afegir a la pantalla d’inici» i confirma-ho amb «Afegir».',
    'Abre el menú «Archivo» de Safari.': 'Obre el menú «Arxiu» de Safari.',
    'Elige «Añadir al Dock».': 'Tria «Afegir al Dock».',
    'Confirma el nombre y pulsa «Añadir».': 'Confirma el nom i prem «Afegir».',
    'No se pudo preparar la instalación de la app. Recarga la página o prueba otro navegador.': 'No s’ha pogut preparar la instal·lació de l’aplicació. Torna a carregar la pàgina o prova un altre navegador.',
    'Perfil de este dispositivo · 150 puntos iniciales y ofertas de prueba. Comercios geolocalizados desde OpenStreetMap.': 'Perfil d’aquest dispositiu · 150 punts inicials i ofertes de prova. Comerços geolocalitzats amb OpenStreetMap.',
    'Vincula tu perfil.': 'Vincula el teu perfil.',
    'Credenciales actualizadas; las otras sesiones se han cerrado.': 'Credencials actualitzades; s’han tancat les altres sessions.',
    'Sesión cerrada.': 'Sessió tancada.',
    'Las contraseñas no coinciden.': 'Les contrasenyes no coincideixen.',
    'Apunta al QR de un cupón VilaCircula.': 'Apunta al QR d’un cupó de VilaCircula.',
    'Ese QR no es un cupón VilaCircula. Sigue enfocando el QR del vale.': 'Aquest QR no és un cupó de VilaCircula. Continua enfocant el QR del val.',
    'Introduce un cupón VC-… o un EcoID VCID-… válido.': 'Introdueix un cupó VC-… o un EcoID VCID-… vàlid.',
    '¡EcoID escaneado correctamente!': 'EcoID escanejat correctament!',
    'Canje de prueba registrado en el servidor.': 'Bescanvi de prova registrat al servidor.',
    'Cupón validado por el servidor.': 'Cupó validat pel servidor.',
    'Meta diaria alcanzada: +30 EcoPunts.': 'Objectiu diari assolit: +30 EcoPunts.',
    'Este navegador no permite leer el acelerómetro. Usa un dispositivo compatible y una conexión segura (HTTPS).': 'Aquest navegador no permet llegir l’acceleròmetre. Fes servir un dispositiu compatible i una connexió segura (HTTPS).',
    'Cupón creado y saldo actualizado en el servidor.': 'Cupó creat i saldo actualitzat al servidor.',
    'Escaneo de prueba registrado en SQLite · +10 EcoPuntos.': 'Escaneig de prova registrat a SQLite · +10 EcoPunts.',
    'Ficha ilustrativa; no es un comercio verificado.': 'Fitxa il·lustrativa; no és un comerç verificat.',
    'Cómo llegar': 'Com arribar-hi',
    'Este navegador no permite consultar la ubicación.': 'Aquest navegador no permet consultar la ubicació.',
    'Esperando permiso de ubicación…': 'Esperant el permís d’ubicació…',
    'Ubicación usada solo en esta sesión; no se envió al servidor.': 'La ubicació només s’ha fet servir en aquesta sessió; no s’ha enviat al servidor.',
    'No se concedió el permiso de ubicación.': 'No s’ha concedit el permís d’ubicació.',
    'No se pudo determinar la ubicación.': 'No s’ha pogut determinar la ubicació.',
    'Notificaciones activadas para recordatorios y promociones.': 'Notificacions activades per als recordatoris i les promocions.',
    'Las notificaciones quedaron desactivadas, pero el panel de alertas seguirá funcionando localmente.': 'Les notificacions estan desactivades, però el tauler d’avisos continuarà funcionant localment.',
    'Inicia sesión para acceder a VilaCircula.': 'Inicia la sessió per accedir a VilaCircula.',
    'API no disponible · comprueba la conexión antes de iniciar sesión.': 'API no disponible · comprova la connexió abans d’iniciar la sessió.',
    'Aún no has escaneado el punto de hoy.': 'Encara no has escanejat el punt d’avui.',
    'Los puntos de EcoRuta se mostrarán al conectarse el servicio municipal.': 'Els punts d’EcoRuta es mostraran quan es connecti el servei municipal.',
    'SALDO DE DEMOSTRACIÓN': 'SALDO DE DEMOSTRACIÓ',
    'Puntos acumulados en los perfiles registrados en esta demo.': 'Punts acumulats als perfils registrats en aquesta demostració.',
    'Puntos sumados por instituto; el ranking no muestra datos personales.': 'Punts sumats per institut; la classificació no mostra dades personals.',
    'Oferta de demostración': 'Oferta de demostració',
    'Apunta al QR de un cupón o EcoID VilaCircula.': 'Apunta al QR d’un cupó o EcoID de VilaCircula.',
    'El QR no es un cupón ni un EcoID VilaCircula.': 'El QR no és un cupó ni un EcoID de VilaCircula.',
    'No pudimos leer el QR. Ajusta el enfoque e inténtalo de nuevo.': 'No hem pogut llegir el QR. Ajusta l’enfocament i torna-ho a provar.',
    'Aquí verás los puntos confirmados por comercios. Explora los locales disponibles para empezar.': 'Aquí veuràs els punts confirmats pels comerços. Explora els establiments disponibles per començar.',
    'Explorar comercios →': 'Explora els comerços →',
    '2 € en pan artesano': '2 € en pa artesà',
    'Descuento en tu próxima compra.': 'Descompte en la propera compra.',
    'Un café de la casa': 'Un cafè de la casa',
    'Un café hecho con calma, por la casa.': 'Un cafè fet amb calma, convidat per la casa.',
    '2 € en material escolar': '2 € en material escolar',
    'Tu próximo proyecto empieza aquí.': 'El teu proper projecte comença aquí.',
    'Cesta de temporada': 'Cistella de temporada',
    'Fruta y verdura de proximidad.': 'Fruita i verdura de proximitat.',
    '10% en moda circular': '10% en moda circular',
    'Estilo con una segunda vida.': 'Estil amb una segona vida.',
    'Planta aromática': 'Planta aromàtica',
    'Un poco más verde para tu casa.': 'Una mica més de verd per a casa teva.',
    'Todos': 'Tots',
    'Alimentación': 'Alimentació',
    'Papelería': 'Papereria',
    'Cafeterías': 'Cafeteries',
    'Moda': 'Moda',
    'Elige un comercio': 'Tria un comerç',
    'Toca una tienda para ver sus iniciativas y recompensas.': 'Toca una botiga per veure’n les iniciatives i recompenses.',
    'Sin ubicación': 'Sense ubicació',
    'Activa ubicación': 'Activa la ubicació',
    'Liga local · 1.º trimestre': 'Lliga local · 1r trimestre',
    'La ciudad juega en equipo.': 'La ciutat juga en equip.',
    'Pequeños gestos, grandes cambios en tu instituto.': 'Petits gestos, grans canvis al teu institut.',
    'ACTUALIZADO AHORA': 'ACTUALITZAT ARA',
    'PUESTO': 'POSICIÓ',
    'INSTITUTO': 'INSTITUT',
    'PUNTOS': 'PUNTS',
    'SEMANA': 'SETMANA',
    'TU HUELLA EN EL EQUIPO': 'LA TEVA PETJADA A L’EQUIP',
    'TU IMPACTO EN VILADECANS': 'EL TEU IMPACTE A VILADECANS',
    'Así ayudas a tu ciudad': 'Així ajudes la teva ciutat',
    'Tu insti cuenta contigo.': 'El teu institut compta amb tu.',
    'Tu constancia suma puntos al Insti Sales y acerca el trofeo a todo el equipo.': 'La teva constància suma punts a l’institut Sales i acosta el trofeu a tot l’equip.',
    'PUNTOS APORTADOS': 'PUNTS APORTATS',
    'EN TU INSTITUTO': 'AL TEU INSTITUT',
    'EL TROFEO SE ENTREGA EN': 'EL TROFEU ES LLIURA D’AQUÍ A',
    'Final de liga': 'Final de lliga',
    'TU MONEDERO LOCAL': 'EL TEU MONEDER LOCAL',
    'EcoPuntos disponibles para ti.': 'EcoPunts disponibles per a tu.',
    '1 € = 30 ECOPUNTOS': '1 € = 30 ECOPUNTS',
    'Vales para disfrutar Viladecans': 'Vals per gaudir de Viladecans',
    'CANJE INSTANTÁNEO': 'BESCANVI IMMEDIAT',
    'Tus cupones activos': 'Els teus cupons actius',
    'VALES': 'VALS',
    'Tu progreso': 'El teu progrés',
    'Insignias y constancia': 'Insígnies i constància',
    'insignias': 'insígnies',
    'día': 'dia',
    'días': 'dies',
    'seguidos': 'seguits',
    'Racha actual · récord': 'Ratxa actual · rècord',
    'CONSEGUIDA': 'ACONSEGUIDA',
    'FACTORES DE CONVERSIÓN': 'FACTORS DE CONVERSIÓ',
    'pasos': 'passos',
    'evitado': 'evitat',
    'evitados': 'evitats',
    '1 compra ECO': '1 compra ECO',
    'compras ECO verificadas': 'compres ECO verificades',
    'CO₂ evitado': 'CO₂ evitat',
    'El CO₂ se estima con acciones verificadas. La sincronización de pasos y EcoRuta todavía no está conectada.': 'El CO₂ s’estima a partir d’accions verificades. La sincronització dels passos i l’EcoRuta encara no està connectada.',
    'Compras ECO verificadas': 'Compres ECO verificades',
    'Pasos registrados': 'Passos registrats',
    'EcoPuntos aportados': 'EcoPunts aportats',
    'km de EcoRuta': 'km d’EcoRuta',
    'Buscar cerca de mí': 'Cerca a prop meu',
    'Modo de demostración': 'Mode de demostració',
    'Sin conexión · puedes consultar lo guardado en este dispositivo.': 'Sense connexió. Pots consultar el que s’ha desat en aquest dispositiu.',
    'Conexión recuperada · sincronizando tu cuenta…': 'Connexió recuperada. S’està sincronitzant el teu compte…',
    'PANEL MUNICIPAL': 'PANEL MUNICIPAL',
    'Dashboard de administración': 'Tauler d’administració',
    'Resumen operativo del impacto y la actividad de VilaCircula.': 'Resum de l’impacte i l’activitat de VilaCircula.',
    'Cargando dashboard…': 'S’està carregant el tauler…',
    'Volver': 'Torna',
    'Perfiles': 'Perfils',
    'activos esta semana': 'actius aquesta setmana',
    'Validaciones': 'Validacions',
    'total registradas': 'total registrades',
    'Éxitos': 'Èxits',
    'cupones validados': 'cupons validats',
    'Caja': 'Caixa',
    'usuarios de comercio': 'usuaris de comerços',
    'Factores de conversión': 'Factors de conversió',
    'Actividad reciente': 'Activitat recent',
    'No hay validaciones todavía': 'Encara no hi ha validacions',
    'sin datos': 'sense dades',
    'PRIMEROS PASOS': 'PRIMERS PASSOS',
    'Empieza en VilaCircula.': 'Comença a VilaCircula.',
    'Tu cuenta ya está lista. En menos de un minuto puedes empezar a usar tus EcoPuntos.': 'El teu compte ja està a punt. En menys d’un minut podràs començar a fer servir els EcoPunts.',
    'Explora': 'Explora',
    'Descubre comercios cercanos y sus iniciativas.': 'Descobreix comerços propers i les seves iniciatives.',
    'Participa': 'Participa',
    'Enséñale tu EcoID al comercio.': 'Ensenya el teu EcoID al comerç.',
    'Disfruta': 'Gaudeix',
    'Canjea tus puntos por recompensas locales.': 'Bescanvia els punts per recompenses locals.',
    'Ver comercios': 'Mostra els comerços',
    'Ahora no': 'Ara no',
    'IDENTIFICACIÓN CIUDADANA': 'IDENTIFICACIÓ CIUTADANA',
    'Tu EcoID dinámico': 'El teu EcoID dinàmic',
    'Cerrar': 'Tanca',
    'VILADECANS · PERFIL CIUDADANO': 'VILADECANS · PERFIL CIUTADÀ',
    'PERFIL CIUDADANO': 'PERFIL CIUTADÀ',
    'Entra en VilaCircula.': 'Entra a VilaCircula.',
    'Usa tu cuenta de Google para continuar.': 'Fes servir el teu compte de Google per continuar.',
    'Tu ciudad, en marcha.': 'La teva ciutat, en marxa.',
    'Inicia sesión con Google para acceder a tu espacio y tus EcoPuntos.': 'Inicia la sessió amb Google per accedir al teu espai i als EcoPunts.',
    'Vincula tu perfil.': 'Vincula el teu perfil.',
    'Nombre o apodo': 'Nom o àlies',
    'Fecha de nacimiento': 'Data de naixement',
    'Tu instituto': 'El teu institut',
    'Selecciona tu instituto': 'Selecciona el teu institut',
    'Código exclusivo del centro': 'Codi exclusiu del centre',
    'Solicita el código a tu centro educativo.': 'Demana el codi al teu centre educatiu.',
    'Crear cuenta con Google': 'Crea un compte amb Google',
    'Vincular un perfil que ya tengo': 'Vincula un perfil que ja tinc',
    'Vincular mi perfil': 'Vincula el meu perfil',
    'Usuario actual de VilaCircula': 'Usuari actual de VilaCircula',
    'Contraseña actual': 'Contrasenya actual',
    'PERFIL VILACIRCULA': 'PERFIL VILACIRCULA',
    'Tu cuenta': 'El teu compte',
    'Editar nombre': 'Edita el nom',
    'Usuario y contraseña': 'Usuari i contrasenya',
    'Zona de caja de comercio': 'Zona de caixa del comerç',
    'Panel municipal': 'Panell municipal',
    'Cerrar sesión': 'Tanca la sessió',
    'Editar perfil': 'Edita el perfil',
    'Guardar cambios': 'Desa els canvis',
    'Cuenta': 'Compte',
    'Validación en caja': 'Validació a caixa',
    'Escanear cupón': 'Escaneja un cupó',
    'Canjear': 'Bescanvia',
    'Cupones canjeados': 'Cupons bescanviats',
    'CANJEADO': 'BESCANVIAT',
    'Ver QR y canjear': 'Mostra el QR i bescanvia',
    'Ver QR de': 'Mostra el QR de',
    'Tus próximos premios aparecerán aquí.': 'Els teus propers premis apareixeran aquí.',
    'Te faltan EcoPuntos para este vale.': 'Et falten EcoPunts per a aquest val.',
    'Monedero VilaCircula': 'Moneder VilaCircula',
    'Escanea un cupón': 'Escaneja un cupó',
    'Canje en el comercio': 'Bescanvi al comerç',
    'No marques tu propio vale como canjeado.': 'No marquis el teu val com a bescanviat.',
    'Apunta al QR de un cupón VilaCircula.': 'Enfoca el QR d’un cupó de VilaCircula.',
    'Ese QR no es un cupón VilaCircula. Sigue enfocando el QR del vale.': 'Aquest QR no és un cupó de VilaCircula. Enfoca el QR del val.',
    'Este QR no corresponde a un cupón activo.': 'Aquest QR no correspon a cap cupó actiu.',
    'Este código ha caducado; preparando otro…': 'Aquest codi ha caducat; se n’està preparant un altre…',
    'El código ha caducado; preparando otro…': 'El codi ha caducat; se n’està preparant un altre…',
    'Este código QR ha caducado. Actualiza la pantalla para generar uno nuevo.': 'Aquest codi QR ha caducat. Actualitza la pantalla per generar-ne un de nou.',
    'No pudimos leer el QR. Ajusta el enfoque e inténtalo de nuevo.': 'No hem pogut llegir el QR. Ajusta l’enfocament i torna-ho a provar.',
    'No hay conexión con VilaCircula. Comprueba tu conexión e inténtalo de nuevo.': 'No hi ha connexió amb VilaCircula. Comprova la connexió i torna-ho a provar.',
    'No se pudo cargar el mapa. Comprueba la conexión para ver las calles de Viladecans.': 'No s’ha pogut carregar el mapa. Comprova la connexió per veure els carrers de Viladecans.',
    'No se pudo cargar el mapa. Comprueba la conexión para ver los comercios.': 'No s’ha pogut carregar el mapa. Comprova la connexió per veure els comerços.',
    'Ubicación contrastada en': 'Ubicació contrastada a',
    'Cómo llegar': 'Com arribar-hi',
    'Oferta de demostración': 'Oferta de demostració',
    'Compra ECO confirmada por el comercio': 'Compra ECO confirmada pel comerç',
    'Debes aceptar la política de privacidad para crear una cuenta de estudiante.': 'Has d’acceptar la Política de Privacitat per crear un compte d’estudiant.',
    'Ejemplo · no confirmado': 'Exemple · no confirmat',
    'Ficha ilustrativa; no es un comercio verificado.': 'Fitxa il·lustrativa; no és un comerç verificat.',
    'Aún no hay compras confirmadas por un comercio.': 'Encara no hi ha compres confirmades per un comerç.',
    'Aquí verás los puntos confirmados por comercios. Explora los locales disponibles para empezar.': 'Aquí veuràs els punts confirmats pels comerços. Explora els establiments disponibles per començar.',
    'Explorar comercios →': 'Explora els comerços →',
    'Compras verificadas': 'Compres verificades',
    'Puntos acumulados en los perfiles registrados en esta demo.': 'Punts acumulats als perfils registrats en aquesta demostració.',
    'Puntos sumados por instituto; el ranking no muestra datos personales.': 'Punts sumats per institut; la classificació no mostra dades personals.',
    'Meta diaria alcanzada. Tus 30 EcoPunts ya están en el saldo.': 'Objectiu diari assolit. Ja tens els 30 EcoPunts al saldo.',
    'Meta diaria alcanzada! Tus 30 EcoPunts ya están en el saldo.': 'Objectiu diari assolit! Ja tens els 30 EcoPunts al saldo.',
    'Contador activo. Mantén VilaCircula abierta para registrar tus pasos.': 'Comptador actiu. Mantén VilaCircula oberta per registrar els passos.',
    'Este navegador no permite leer el acelerómetro. Usa un dispositivo compatible y una conexión segura (HTTPS).': 'Aquest navegador no permet llegir l’acceleròmetre. Fes servir un dispositiu compatible i una connexió segura (HTTPS).',
    'Da permiso al acelerómetro para contar pasos.': 'Dona permís a l’acceleròmetre per comptar els passos.',
    'No se pudo activar el contador de pasos.': 'No s’ha pogut activar el comptador de passos.',
    'Permite el acceso a la cámara para escanear el cupón.': 'Permet l’accés a la càmera per escanejar el cupó.',
    'Introduce un cupón VC-… o un EcoID VCID-… válido.': 'Introdueix un cupó VC-… o un EcoID VCID-… vàlid.',
    'El escaneo se confirmó, pero no se pudo actualizar el saldo. Recarga la app para ver los puntos.': 'S’ha confirmat l’escaneig, però no s’ha pogut actualitzar el saldo. Torna a carregar l’aplicació per veure els punts.',
    'El código QR ha caducado. Genera uno nuevo y vuelve a escanearlo.': 'El codi QR ha caducat. Genera’n un de nou i torna’l a escanejar.',
    'No se pudo completar la solicitud. Comprueba los datos e inténtalo de nuevo.': 'No s’ha pogut completar la sol·licitud. Comprova les dades i torna-ho a provar.',
    'No se pudo cargar el acceso seguro de Google.': 'No s’ha pogut carregar l’accés segur de Google.',
    'El CO₂ se estima con acciones verificadas. La sincronización de pasos y EcoRuta todavía no está conectada.': 'El CO₂ s’estima a partir d’accions verificades. La sincronització dels passos i l’EcoRuta encara no està connectada.',
    'Revisa los datos del formulario y vuelve a intentarlo.': 'Revisa les dades del formulari i torna-ho a provar.',
    'No tienes permiso para hacer esta acción.': 'No tens permís per fer aquesta acció.',
    'La sesión no es válida o ha caducado. Vuelve a iniciar sesión.': 'La sessió no és vàlida o ha caducat. Torna a iniciar la sessió.',
    'Ha ocurrido un error. Inténtalo de nuevo.': 'S’ha produït un error. Torna-ho a provar.',
    'El día de actividad ha cambiado. Sincroniza el contador actualizado.': 'Ha canviat el dia d’activitat. Sincronitza el comptador actualitzat.',
    'Actividad del dispositivo': 'Activitat del dispositiu',
    'El cajero lo escanea para añadir 10 EcoPuntos a tu cuenta. Cada código solo sirve una vez.': 'La persona de caixa l’escaneja per afegir 10 EcoPunts al teu compte. Cada codi només es pot fer servir una vegada.',
    'Preparando código…': 'S’està preparant el codi…',
    'Conectando para confirmar el escaneo…': 'S’està connectant per confirmar l’escaneig…',
    'El código ha caducado; preparando otro…': 'El codi ha caducat; se n’està preparant un altre…',
    '¡EcoID escaneado correctamente!': 'EcoID escanejat correctament!',
    'Se han añadido 10 EcoPuntos a tu cuenta.': 'S’han afegit 10 EcoPunts al teu compte.',
    '¡Meta diaria alcanzada! Tus 30 EcoPunts ya están en el saldo.': 'Objectiu diari assolit! Ja tens els 30 EcoPunts al saldo.',
    'La conexión se ha interrumpido. Mantén esta pantalla abierta; volveremos a intentarlo.': 'S’ha interromput la connexió. Mantén aquesta pantalla oberta; ho tornarem a provar.',
    'No se pudo generar el código. Se volverá a intentar automáticamente.': 'No s’ha pogut generar el codi. Ho tornarem a provar automàticament.',
    'Código listo. Se actualizará automáticamente para proteger tu cuenta.': 'Codi a punt. S’actualitzarà automàticament per protegir el teu compte.',
    'Solicitud de alta de comercio': 'Sol·licitud d’alta de comerç',
    'Establecimiento': 'Establiment',
    'Ubicación pública': 'Ubicació pública',
    'Consentimiento: autorizo mostrar el nombre, logotipo y ubicación en el directorio público.': 'Consentiment: autoritzo que es mostrin el nom, el logotip i la ubicació al directori públic.',
    'Da de alta tu comercio.': 'Dona d’alta el teu comerç.',
    'Prepara una solicitud para revisar la incorporación del establecimiento al directorio público.': 'Prepara una sol·licitud perquè revisem la incorporació de l’establiment al directori públic.',
    'Nombre del establecimiento': 'Nom de l’establiment',
    'URL del logotipo': 'URL del logotip',
    'Ubicación que se mostrará': 'Ubicació que es mostrarà',
    'Correo de contacto': 'Correu de contacte',
    'Autorizo a VilaCircula a mostrar el nombre, logotipo y ubicación del establecimiento en el directorio público.': 'Autoritzo VilaCircula a mostrar el nom, el logotip i la ubicació de l’establiment al directori públic.',
    'La solicitud se revisará antes de publicar el establecimiento.': 'Revisarem la sol·licitud abans de publicar l’establiment.',
    'Política de Privacitat': 'Política de Privacitat',
    'Preparar solicitud': 'Prepara la sol·licitud',
    'Se abrirá tu aplicación de correo. Envía el mensaje para completar la solicitud; la publicación requiere revisión.': 'S’obrirà l’aplicació de correu. Envia el missatge per completar la sol·licitud; cal revisar-la abans de publicar.',
    'Política de Privacitat & RGPD': 'Política de Privacitat i RGPD',
    'Termes d’ús i prevenció de frau': 'Termes d’ús i prevenció del frau',
    'Política de Galetes': 'Política de Galetes',
    'Alta de comerços': 'Alta de comerços',
    'Política de Privacitat & RGPD': 'Política de Privacitat i RGPD',
    'Privacitat, termes i galetes | VilaCircula': 'Privacitat, termes i galetes | VilaCircula',
    'Información legal': 'Informació legal',
    'Política de Privacitat & RGPD': 'Política de Privacitat i RGPD',
    'Responsable:': 'Responsable:',
    'Dades tractades:': 'Dades tractades:',
    'Minimització:': 'Minimització:',
    'Drets de les persones usuàries:': 'Drets de les persones usuàries:',
    'Idioma': 'Idioma',
    'Idioma de la aplicación': 'Idioma de la aplicación'
  };

  const catalanToSpanish = {
    'Informació legal': 'Información legal',
    'Política de Privacitat i RGPD': 'Política de Privacidad y RGPD',
    'Termes d’ús i prevenció del frau': 'Términos de uso y prevención del fraude',
    'Termes d’Ús i Prevenció de Frau': 'Términos de uso y prevención del fraude',
    'Política de Galetes': 'Política de cookies',
    'Política de Galetes (cookies)': 'Política de cookies',
    'Alta de comerços': 'Alta de comercios',
    '← Torna a VilaCircula': '← Volver a VilaCircula',
    'Política de Privacitat i RGPD': 'Política de Privacidad y RGPD',
    'Termes d’ús i prevenció del frau': 'Términos de uso y prevención del fraude',
    'Termes d’Ús i Prevenció del Frau': 'Términos de uso y prevención del fraude',
    'Política de Galetes': 'Política de cookies',
    'Política de Galetes (cookies)': 'Política de cookies',
    'Alta de comerços': 'Alta de comercios',
    '← Torna a VilaCircula': '← Volver a VilaCircula',
    'VilaCircula | Ciutat sostenible': 'VilaCircula | Ciudad sostenible',
    'Guanya i bescanvia EcoPunts a Viladecans.': 'Gana y canjea EcoPuntos en Viladecans.',
    'Privacitat, termes i galetes | VilaCircula': 'Privacidad, términos y cookies | VilaCircula',
    'Informació sobre les dades, l’ús de la plataforma i les galetes.': 'Información sobre los datos, el uso de la plataforma y las cookies.',
    'Política de Privacitat i RGPD': 'Política de Privacidad y RGPD',
    'Termes d’Ús i Prevenció del Frau': 'Términos de uso y prevención del fraude',
    'Política de Galetes (cookies)': 'Política de cookies',
    '← Torna a VilaCircula': '← Volver a VilaCircula',
    'VilaCircula (Projecte Talent a les Aules).': 'VilaCircula (Proyecto Talent a les Aules).',
    'correu electrònic (@xtec.cat o personal), nom o àlies, centre educatiu, data de naixement (només per assignar el rol) i historial d’EcoPunts. Si ets estudiant, també conservem la data d’acceptació de la Política de Privacitat. Per gestionar sol·licituds d’alta comercial, també es poden tractar les dades de contacte i la informació de l’establiment que ens enviï el comerç.': 'correo electrónico (@xtec.cat o personal), nombre o alias, centro educativo, fecha de nacimiento (solo para asignar el rol) e historial de EcoPuntos. Si eres estudiante, también conservamos la fecha de aceptación de la Política de Privacidad. Para gestionar solicitudes de alta comercial, también pueden tratarse los datos de contacto y la información del establecimiento que nos envíe el comercio.',
    'no demanem dades innecessàries com el DNI, l’adreça personal o el telèfon. La ubicació sol·licitada als comerços és la de l’establiment que volen mostrar al directori.': 'no pedimos datos innecesarios como el DNI, la dirección personal o el teléfono. La ubicación solicitada a los comercios es la del establecimiento que quieren mostrar en el directorio.',
    'Les dades s’utilitzen per gestionar el compte, la sessió, els EcoPunts, la participació a la lliga d’instituts i les sol·licituds comercials.': 'Los datos se utilizan para gestionar la cuenta, la sesión, los EcoPuntos, la participación en la liga de institutos y las solicitudes comerciales.',
    'pots sol·licitar l’eliminació del compte escrivint a': 'puedes solicitar la eliminación de la cuenta escribiendo a',
    'El compte i els EcoPunts són d’ús personal i no transferible.': 'La cuenta y los EcoPuntos son de uso personal e intransferible.',
    'Es prohibeix reproduir o utilitzar codis QR mitjançant captures de pantalla. Davant indicis de frau, el sistema pot bloquejar automàticament el compte.': 'Se prohíbe reproducir o utilizar códigos QR mediante capturas de pantalla. Ante indicios de fraude, el sistema puede bloquear automáticamente la cuenta.',
    'VilaCircula és la plataforma tecnològica. La disponibilitat de productes, descomptes i recompenses depèn de cada comerç adherit.': 'VilaCircula es la plataforma tecnológica. La disponibilidad de productos, descuentos y recompensas depende de cada comercio adherido.',
    'VilaCircula només utilitza galetes tècniques i emmagatzematge local del navegador (': 'VilaCircula solo utiliza cookies técnicas y almacenamiento local del navegador (',
    ') per mantenir la sessió oberta i recordar l’estat necessari de l’aplicació.': ') para mantener la sesión abierta y recordar el estado necesario de la aplicación.',
    'No fem servir galetes de seguiment ni galetes publicitàries de tercers.': 'No utilizamos cookies de seguimiento ni cookies publicitarias de terceros.',
    'Ves al contingut principal': 'Ir al contenido principal',
    'Logotip de': 'Logotipo de',
    'Idioma de l’aplicació': 'Idioma de la aplicación',
    'Codi QR del cupó': 'Código QR del cupón',
    'Logotip de': 'Logotipo de',
    'Imatge de': 'Imagen de',
    'Imatge de VilaCircula': 'Imagen de VilaCircula'
  };

  const originalText = new WeakMap();
  const appliedText = new WeakMap();
  const originalAttributes = new WeakMap();
  const appliedAttributes = new WeakMap();
  const reverseTranslations = Object.fromEntries(
    Object.entries(translations)
      .filter(([spanish, catalan]) => spanish !== catalan)
      .map(([spanish, catalan]) => [catalan, spanish])
  );
  const localeFromStorage = localStorage.getItem(LANGUAGE_KEY);
  let language = localeFromStorage === 'es' ? 'es' : 'ca';

  function locale() {
    return language === 'ca' ? 'ca-ES' : 'es-ES';
  }

  function translateText(value) {
    const trimmed = value.trim();
    if (!trimmed) return value;
    if (catalanToSpanish[trimmed]) return value;
    if (language === 'ca' && reverseTranslations[trimmed]) return value;
    let translated = translations[trimmed] || trimmed;
    if (translated === trimmed) {
      translated = trimmed
        .replace(/^Buenas noches,?\s*/, 'Bona nit, ')
        .replace(/^Buenos días,?\s*/, 'Bon dia, ')
        .replace(/^Buenas tardes,?\s*/, 'Bona tarda, ')
        .replace(/\bEcoPuntos\b/g, 'EcoPunts')
        .replace(/\bpasos\b/g, 'passos')
        .replace(/\bcomercios\b/g, 'comerços')
        .replace(/\bComercios\b/g, 'Comerços')
        .replace(/Alimentación · Zero waste/g, 'Alimentació · residu zero')
        .replace(/Papelería · Material escolar/g, 'Papereria · material escolar')
        .replace(/Cafetería · Café de especialidad/g, 'Cafeteria · cafè d’especialitat')
        .replace(/Moda · Segunda mano/g, 'Moda · segona mà')
        .replace(/Panadería · Artesana/g, 'Forn · artesà')
        .replace(/Librería · Cultural/g, 'Llibreria · cultural')
        .replace(/Ubicación no disponible/g, 'Ubicació no disponible')
        .replace(/\bCanjear\b/g, 'Bescanviar')
        .replace(/\bCanjeado\b/g, 'Bescanviat')
        .replace(/\bCanjeados\b/g, 'Bescanviats')
        .replace(/\bCupón\b/g, 'Cupó')
        .replace(/\bcupones\b/g, 'cupons')
        .replace(/\bCupones\b/g, 'Cupons')
        .replace(/\binstituto\b/g, 'institut')
        .replace(/\binstitutos\b/g, 'instituts')
        .replace(/\bInstituto\b/g, 'Institut')
        .replace(/\bPuntos\b/g, 'Punts')
        .replace(/\bFaltan\b/g, 'Et falten');
    }
    return value.replace(trimmed, translated);
  }

  function translateToSpanish(value) {
    const trimmed = value.trim();
    if (!trimmed) return value;
    let translated = catalanToSpanish[trimmed] || reverseTranslations[trimmed];
    if (!translated) {
      translated = trimmed
        .replace(/^Logotip de /, 'Logotipo de ')
        .replace(/^Codi QR de /, 'Código QR de ')
        .replace(/^Codi QR del /, 'Código QR del ')
        .replace(/\bEcoPunts\b/g, 'EcoPuntos')
        .replace(/\bcomerços\b/g, 'comercios')
        .replace(/\bComerços\b/g, 'Comercios')
        .replace(/\bpassos\b/g, 'pasos')
        .replace(/\bevitats\b/g, 'evitados')
        .replace(/\bevitat\b/g, 'evitado')
        .replace(/d’EcoRuta/g, 'de EcoRuta')
        .replace(/Alimentació · residu zero/g, 'Alimentación · Zero waste')
        .replace(/Papereria · material escolar/g, 'Papelería · Material escolar')
        .replace(/Cafeteria · cafè d’especialitat/g, 'Cafetería · Café de especialidad')
        .replace(/Moda · segona mà/g, 'Moda · Segunda mano')
        .replace(/Forn · artesà/g, 'Panadería · Artesana')
        .replace(/Llibreria · cultural/g, 'Librería · Cultural')
        .replace(/Ubicació no disponible/g, 'Ubicación no disponible')
        .replace(/\bBescanviats\b/g, 'Canjeados')
        .replace(/\bBescanviat\b/g, 'Canjeado')
        .replace(/\bBescanviar\b/g, 'Canjear')
        .replace(/\bBescanvia\b/g, 'Canjea')
        .replace(/\bBescanvi\b/g, 'Canje')
        .replace(/\bCupons\b/g, 'Cupones')
        .replace(/\bcupons\b/g, 'cupones')
        .replace(/\bLliga\b/g, 'Liga')
        .replace(/\bliga\b/g, 'liga')
        .replace(/\binstitut\b/g, 'instituto')
        .replace(/\bInstitut\b/g, 'Instituto')
        .replace(/\bPunts\b/g, 'Puntos')
        .replace(/\bpunts\b/g, 'puntos')
        .replace(/\bcodi\b/g, 'código')
        .replace(/\bCodi\b/g, 'Código')
        .replace(/\bcompte\b/g, 'cuenta')
        .replace(/\bCompte\b/g, 'Cuenta');
    }
    return value.replace(trimmed, translated);
  }

  function translateTextNode(node) {
    const current = node.nodeValue;
    const last = appliedText.get(node);
    if (last !== undefined && current !== last) originalText.set(node, current);
    if (!originalText.has(node)) originalText.set(node, current);
    const original = originalText.get(node);
    const next = language === 'ca' ? translateText(original) : translateToSpanish(original);
    if (current !== next) {
      node.nodeValue = next;
      appliedText.set(node, next);
    } else {
      appliedText.set(node, current);
    }
  }

  function translateAttribute(element, attribute) {
    const current = element.getAttribute(attribute);
    if (current === null) return;
    let originals = originalAttributes.get(element);
    let applied = appliedAttributes.get(element);
    if (!originals) {
      originals = new Map();
      applied = new Map();
      originalAttributes.set(element, originals);
      appliedAttributes.set(element, applied);
    }
    if (applied.has(attribute) && current !== applied.get(attribute)) originals.set(attribute, current);
    if (!originals.has(attribute)) originals.set(attribute, current);
    const original = originals.get(attribute);
    const next = language === 'ca' ? translateText(original) : translateToSpanish(original);
    if (current !== next) element.setAttribute(attribute, next);
    applied.set(attribute, next);
  }

  function translateTree(root) {
    if (root.nodeType === Node.TEXT_NODE) {
      translateTextNode(root);
      return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(textNode) {
        return textNode.parentElement?.closest('script, style, noscript, textarea')
          ? NodeFilter.FILTER_REJECT
          : NodeFilter.FILTER_ACCEPT;
      }
    });
    let node;
    while ((node = walker.nextNode())) translateTextNode(node);
    const elements = root instanceof Document
      ? [...root.querySelectorAll('*')]
      : [root, ...root.querySelectorAll('*')];
    for (const element of elements) {
      if (element.matches('i[data-lucide], svg.lucide')) element.setAttribute('aria-hidden', 'true');
      if (element.classList.contains('merchant-logo') && !element.hasAttribute('aria-label')) {
        const merchantName = element.closest('[data-shop]')?.getAttribute('data-shop')
          || element.closest('.merchant')?.querySelector('.merchant-info strong')?.textContent
          || 'comerç';
        element.setAttribute('role', 'img');
        element.setAttribute('aria-label', `Logotip de ${merchantName}`);
      }
      if (
        element.matches('.coupon-large-qr, #live-ecoid-qr, #qr-code')
        && !element.hasAttribute('aria-label')
      ) {
        element.setAttribute('role', 'img');
        element.setAttribute('aria-label', 'Codi QR de VilaCircula');
      }
      if (element instanceof HTMLImageElement && !element.hasAttribute('alt')) {
        const merchant = element.closest('[data-shop]')?.getAttribute('data-shop');
        element.alt = merchant
          ? `Logotipo de ${merchant}`
          : element.closest('.coupon-large-qr, .coupon-qr')
            ? 'Codi QR del cupó'
            : 'Imatge de VilaCircula';
      }
      for (const attribute of ['aria-label', 'aria-description', 'alt', 'title', 'placeholder', 'content']) {
        translateAttribute(element, attribute);
      }
    }
  }

  function applyLanguage(nextLanguage) {
    language = nextLanguage === 'es' ? 'es' : 'ca';
    localStorage.setItem(LANGUAGE_KEY, language);
    document.documentElement.lang = language;
    translateTree(document);
    const selector = document.querySelector('#language-switcher');
    if (selector) selector.value = language;
    window.dispatchEvent(new CustomEvent('vilacircula:languagechange', { detail: { language } }));
  }

  function addLanguageSelector() {
    if (document.querySelector('#language-switcher')) return;
    const label = document.createElement('label');
    label.className = 'language-switcher';
    label.htmlFor = 'language-switcher';
    label.innerHTML = '<span>Idioma</span><select id="language-switcher" aria-label="Idioma de la aplicación"><option value="ca">Català</option><option value="es">Castellano</option></select>';
    document.body.insertBefore(label, document.body.firstElementChild);
    label.querySelector('select').addEventListener('change', event => applyLanguage(event.currentTarget.value));
  }

  const accessibilityStyle = document.createElement('link');
  accessibilityStyle.rel = 'stylesheet';
  accessibilityStyle.href = './accessibility.css?v=1';
  document.head.append(accessibilityStyle);

  function addSkipLink() {
    const skip = document.createElement('a');
    skip.className = 'skip-link';
    skip.href = '#main-content';
    skip.textContent = 'Ves al contingut principal';
    document.body.prepend(skip);
    const main = document.querySelector('main');
    if (main) {
      main.id ||= 'main-content';
      main.tabIndex = -1;
    }
  }

  function focusableIn(dialog) {
    return [...dialog.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')]
      .filter(element => element.getClientRects().length > 0);
  }

  document.addEventListener('keydown', event => {
    const dialog = document.querySelector('.modal-backdrop [role="dialog"]');
    if (!dialog) return;
    const focusable = focusableIn(dialog);
    if (event.key === 'Tab' && focusable.length) {
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });

  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'characterData') translateTextNode(record.target);
      else if (record.type === 'attributes') {
        if (record.attributeName) translateAttribute(record.target, record.attributeName);
      } else {
        record.addedNodes.forEach(node => {
          translateTree(node);
          if (node instanceof HTMLElement && node.matches('.modal-backdrop')) {
            requestAnimationFrame(() => {
              const dialog = node.querySelector('[role="dialog"]');
              const focusable = dialog && focusableIn(dialog);
              if (focusable?.length && !dialog.contains(document.activeElement)) focusable[0].focus();
            });
          }
        });
      }
    }
  });

  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const dialog = document.querySelector('.modal-backdrop [role="dialog"]');
    dialog?.querySelector('.modal-close')?.click();
  });
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['aria-label', 'aria-description', 'alt', 'title', 'placeholder', 'content'],
    childList: true,
    characterData: true,
    subtree: true
  });

  window.vilaLocale = locale;
  window.vilaLanguage = () => language;
  window.vilaTranslate = value => language === 'ca'
    ? translateText(String(value))
    : translateToSpanish(String(value));
  addLanguageSelector();
  addSkipLink();
  applyLanguage(language);
})();
