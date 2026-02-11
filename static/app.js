// ===============================
// REFERENCIAS DOM
// ===============================
const form = document.getElementById("formPostulante");
const msg = document.getElementById("msg");
const btnSubmit = document.getElementById("btnSubmit");

// Campos del formulario
const area = document.getElementById("area"); 
const convocatoria = document.getElementById("convocatoria");
const apellidos = document.getElementById("apellidos"); // ✅ CAMPO SEPARADO
const nombres = document.getElementById("nombres"); // ✅ CAMPO SEPARADO
const tipoDoc = document.getElementById("tipo_documento");
const numDoc = document.getElementById("numero_documento");
const fechaNacimiento = document.getElementById("fecha_nacimiento");
const sexo = document.getElementById("sexo");
const celular = document.getElementById("celular");
const correo = document.getElementById("correo");
const fuerzasArmadas = document.getElementById("fuerzas_armadas");
const tieneDiscapacidad = document.getElementById("tiene_discapacidad");
const tipoDiscapacidad = document.getElementById("tipo_discapacidad");
const rowTipoDiscapacidad = document.getElementById("row_tipo_discapacidad");
const privacidad = document.getElementById("privacidad");

// Progreso
const progressBar = document.getElementById("progressBar");
const progressCount = document.getElementById("progressCount");

// ===============================
// DATOS DE CONVOCATORIAS POR ÁREA
// ===============================
const convocatoriasPorArea = {
  'GGRD': [
    'N°001-2026 SUPERVISOR (A) DE PREVENCIONISTA EN GESTIÓN DEL RIESGO DE DESASTRES',
    'N°002-2026 PREVENCIONISTA EN GESTIÓN DEL RIESGO DE DESASTRES',
    'N°003-2026 NOTIFICADOR (A)',
    'N°004-2026 CHOFER',
    'N°005-2026 ESPECIALISTA DE CAMPO EN PREVENCIÓN, REDUCCIÓN Y RECONSTRUCCIÓN',
    'N°006-2026 ESPECIALISTA DE CAMPO EN PREPARACIÓN Y PREVENCIÓN',
    'N°007-2026 ENCARGADO DE FLOTA VEHÍCULAR',
    'N°008-2026 CAPACITADOR EN DEFENSA CIVIL',
    'N°009-2026 OPERADOR DEL MÓDULO DE COMUNICACIONES DEL CENTRO DE OPERACIONES DE EMERGENCIA REGIONAL',
    'N°010-2026 OPERADOR DEL MÓDULO DE OPERACIONES DEL CENTRO DE OPERACIONES DE EMERGENCIA REGIONAL',
    'N°011-2026 OPERADOR DEL MÓDULO DE MONITOREO Y ANÁLISIS DEL CENTRO DE OPERACIONES DE EMERGENCIA REGIONAL',
    'N°012-2026 INGENIERO CIVIL',
    'N°013-2026 INSPECTOR TÉCNICO DE SEGURIDAD EN EDIFICACIONES'
  ],
  'GSCGA': [
    'N°014-2026 OPERARIO DE BARRIDO',
    'N°015-2026 OPERARIOS DE RECOLECCION DE RESIDUOS SOLIDOS',
    'N°016-2026 AYUDANTES DE CONSTRUCCIÓN',
    'N°017-2026 AYUDANTES DE TECNICO ELECTRICISTA',
    'N°018-2026 OPERARIOS DE APOYO DE JARDINERÍA',
    'N°019-2026 PODADOR DE ARBOLES'
  ],
  'GFC': [
    'N°020-2026 INSPECTOR MUNICIPAL',
    'N°021-2026 INSPECTOR DE GIR',
    'N°022-2026 SUPERVISOR DE CAMPO'
  ],
  'GSC': [
    'N°023-2026 SERENO A PIE',
    'N°024-2026 OPERADOR(A) DE CAMARAS DE VIDEOVIGILANCIA',
    'N°025-2026 SERENO TACTICO - UNOES',
    'N°026-2026 SERENO MOTORIZADO',
    'N°027-2026 SERENO CHOFER',
    'N°028-2026 SUPERVISOR(A) CECOP',
    'N°029-2026 SUPERVISOR(A)',
    'N°030-2026 INGENIERO ELECTRÓNICO'
  ],
  'GDE': [
    'N°031-2026 APOYO OPERATIVO',
    'N°032-2026 AUXILIAR AUDIOVISUAL',
    'N°033-2026 AUXILIAR DE TRABAJOS DE CAMPO',
    'N°034-2026 CHOFER',
    'N°035-2026 COORDINADOR AUDIOVISUAL',
    'N°036-2026 COORDINADOR DE CAMPO',
    'N°037-2026 COORDINADOR TÉCNICO DE CAMPO',
    'N°038-2026 GUARDIÁN',
    'N°039-2026 GUIA TURÍSTICO 1',
    'N°040-2026 GUIA TURÍSTICO 2',
    'N°041-2026 INSPECTOR DE RECOJO DE INFORMACIÓN DE CAMPO',
    'N°042-2026 NOTIFICADOR',
    'N°043-2026 OPERARIO DE MANTENIMIENTO DE INFRAESTRUCTURA',
    'N°044-2026 OPERARIO DE MANTENIMIENTO Y LIMPIEZA DE INMUEBLES',
    'N°045-2026 OPERARIO DE PARQUEO VEHICULAR',
    'N°046-2026 OPERARIO DE LIMPIEZA Y COBRANZA DE BAÑOS PÚBLICOS',
    'N°047-2026 ORIENTADORES',
    'N°048-2026 SUPERVISOR DE ACTIVIDADES DE CAMPO',
    'N°049-2026 SUPERVISOR DE TRABAJO DE CAMPO',
    'N°050-2026 SUPERVISOR TÉCNICO'
  ]
};

// ===============================
// CONFIGURACIÓN INICIAL
// ===============================
function inicializar() {
  // Configurar límites de fecha (18-100 años)
  const hoy = new Date();
  const hace18Anos = new Date(hoy.getFullYear() - 18, hoy.getMonth(), hoy.getDate());
  const hace100Anos = new Date(hoy.getFullYear() - 100, hoy.getMonth(), hoy.getDate());
  
  fechaNacimiento.max = hace18Anos.toISOString().split('T')[0];
  fechaNacimiento.min = hace100Anos.toISOString().split('T')[0];
  
  // Inicializar selector de convocatorias
  inicializarSelectorConvocatorias();
  
  // Actualizar progreso inicial
  actualizarProgreso();
}

// ===============================
// SELECTOR DINÁMICO DE CONVOCATORIAS
// ===============================
function inicializarSelectorConvocatorias() {
  if (!area || !convocatoria) {
    console.error('No se encontraron los elementos de área o convocatoria');
    return;
  }

  // Event listener para el cambio de área
  area.addEventListener('change', function() {
    const areaSeleccionada = this.value;
    
    // Limpiar el select de convocatoria
    convocatoria.innerHTML = '<option value="" selected disabled>Seleccione una convocatoria</option>';
    
    // Si hay un área seleccionada, cargar sus convocatorias
    if (areaSeleccionada && convocatoriasPorArea[areaSeleccionada]) {
      // Habilitar el select
      convocatoria.disabled = false;
      
      // Agregar las opciones correspondientes
      convocatoriasPorArea[areaSeleccionada].forEach(conv => {
        const option = document.createElement('option');
        option.value = conv;
        option.textContent = conv;
        convocatoria.appendChild(option);
      });
    } else {
      // Deshabilitar el select si no hay área seleccionada
      convocatoria.disabled = true;
      convocatoria.innerHTML = '<option value="" selected disabled>Primero seleccione un área</option>';
    }
    
    // Resetear el valor seleccionado
    convocatoria.value = '';
    limpiarError(convocatoria);
    
    // Actualizar progreso
    actualizarProgreso();
  });
}

// ===============================
// BARRA DE PROGRESO
// ===============================
function actualizarProgreso() {
  const camposObligatorios = [
    area, 
    convocatoria,
    apellidos, // ✅ ACTUALIZADO
    nombres,   // ✅ ACTUALIZADO
    tipoDoc,
    numDoc,
    fechaNacimiento,
    sexo,
    celular,
    correo,
    fuerzasArmadas,
    tieneDiscapacidad
  ];
  
  const completados = camposObligatorios.filter(campo => {
    const valor = campo.value.trim();
    return valor !== '';
  }).length;
  
  const total = camposObligatorios.length;
  const porcentaje = (completados / total) * 100;
  
  progressBar.style.width = porcentaje + '%';
  progressCount.textContent = completados;
}

// ===============================
// MENSAJES Y TOASTS
// ===============================
function setMsg(text, ok = true) {
  if (!text) {
    msg.style.display = "none";
    msg.textContent = "";
    return;
  }
  
  msg.textContent = text;
  msg.className = "msg " + (ok ? "ok" : "err");
  msg.style.display = "block";
}

function showToastSuccess(message) {
  const wrap = document.getElementById("toastWrap");
  if (!wrap) return;

  const t = document.createElement("div");
  t.className = "toast";
  t.innerHTML = `
    <div class="toast-dot"></div>
    <div>
      <div class="toast-title">Registro exitoso</div>
      <div class="toast-msg">${message}</div>
    </div>
  `;
  wrap.appendChild(t);

  setTimeout(() => {
    t.classList.add("out");
    setTimeout(() => t.remove(), 180);
  }, 2600);
}

function showToastError(message) {
  const wrap = document.getElementById("toastWrap");
  if (!wrap) return;

  const t = document.createElement("div");
  t.className = "toast toast-error";
  t.innerHTML = `
    <div class="toast-dot"></div>
    <div>
      <div class="toast-title">Error</div>
      <div class="toast-msg">${message}</div>
    </div>
  `;
  wrap.appendChild(t);

  setTimeout(() => {
    t.classList.add("out");
    setTimeout(() => t.remove(), 180);
  }, 3000);
}

// ===============================
// VALIDACIONES INDIVIDUALES
// ===============================

// Validar área 
function validarArea() {
  if (!area.value) {
    mostrarError(area, "Debe seleccionar un área");
    return false;
  }
  limpiarError(area);
  return true;
}

// Validar convocatoria
function validarConvocatoria() {
  if (!convocatoria.value) {
    mostrarError(convocatoria, "Debe seleccionar una convocatoria");
    return false;
  }
  limpiarError(convocatoria);
  return true;
}

// ✅ Validar apellidos
function validarApellidos() {
  const valor = apellidos.value.trim();
  
  if (!valor) {
    mostrarError(apellidos, "Ingrese sus apellidos");
    return false;
  }
  
  if (valor.length < 3) {
    mostrarError(apellidos, "Debe tener al menos 3 caracteres");
    return false;
  }
  
  if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(valor)) {
    mostrarError(apellidos, "Solo se permiten letras y espacios");
    return false;
  }
  
  limpiarError(apellidos);
  return true;
}

// ✅ Validar nombres
function validarNombres() {
  const valor = nombres.value.trim();
  
  if (!valor) {
    mostrarError(nombres, "Ingrese sus nombres");
    return false;
  }
  
  if (valor.length < 2) {
    mostrarError(nombres, "Debe tener al menos 2 caracteres");
    return false;
  }
  
  if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(valor)) {
    mostrarError(nombres, "Solo se permiten letras y espacios");
    return false;
  }
  
  limpiarError(nombres);
  return true;
}

// Validar tipo de documento
function validarTipoDocumento() {
  if (!tipoDoc.value) {
    mostrarError(tipoDoc, "Seleccione el tipo de documento");
    return false;
  }
  limpiarError(tipoDoc);
  return true;
}

// Validar número de documento
function validarNumeroDocumento() {
  const tipo = tipoDoc.value;
  const numero = numDoc.value.trim();
  
  if (!tipo) {
    mostrarError(numDoc, "Primero seleccione el tipo de documento");
    return false;
  }
  
  if (!numero) {
    mostrarError(numDoc, "Ingrese el número de documento");
    return false;
  }
  
  if (tipo === "DNI") {
    if (!/^[0-9]{8}$/.test(numero)) {
      mostrarError(numDoc, "El DNI debe tener exactamente 8 dígitos");
      return false;
    }
  } else if (tipo === "CE") {
    if (!/^[0-9]{9}$/.test(numero)) {
      mostrarError(numDoc, "El CE debe tener exactamente 9 dígitos");
      return false;
    }
  }
  
  limpiarError(numDoc);
  return true;
}

// Validar fecha de nacimiento
function validarFechaNacimiento() {
  const valor = fechaNacimiento.value;
  
  if (!valor) {
    mostrarError(fechaNacimiento, "Ingrese su fecha de nacimiento");
    return false;
  }
  
  const fecha = new Date(valor);
  const hoy = new Date();
  
  let edad = hoy.getFullYear() - fecha.getFullYear();
  const mes = hoy.getMonth() - fecha.getMonth();
  
  if (mes < 0 || (mes === 0 && hoy.getDate() < fecha.getDate())) {
    edad--;
  }
  
  if (edad < 18) {
    mostrarError(fechaNacimiento, "Debe ser mayor de 18 años");
    return false;
  }
  
  if (edad > 100) {
    mostrarError(fechaNacimiento, "Fecha inválida");
    return false;
  }
  
  limpiarError(fechaNacimiento);
  return true;
}

// Validar sexo
function validarSexo() {
  if (!sexo.value) {
    mostrarError(sexo, "Seleccione su sexo");
    return false;
  }
  limpiarError(sexo);
  return true;
}

// Validar celular
function validarCelular() {
  const valor = celular.value.trim();
  
  if (!valor) {
    mostrarError(celular, "Ingrese su número de celular");
    return false;
  }
  
  if (!/^[0-9]{9}$/.test(valor)) {
    mostrarError(celular, "El celular debe tener exactamente 9 dígitos");
    return false;
  }
  
  if (!valor.startsWith('9')) {
    mostrarError(celular, "El celular debe empezar con 9");
    return false;
  }
  
  limpiarError(celular);
  return true;
}

// Validar correo
function validarCorreo() {
  const valor = correo.value.trim();
  
  if (!valor) {
    mostrarError(correo, "Ingrese su correo electrónico");
    return false;
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(valor)) {
    mostrarError(correo, "Ingrese un correo válido");
    return false;
  }
  
  limpiarError(correo);
  return true;
}

// Validar checkbox de privacidad
function validarPrivacidad() {
  if (!privacidad.checked) {
    const errorSpan = document.querySelector('.privacy-error');
    if (errorSpan) {
      errorSpan.textContent = "Debe aceptar la política de privacidad";
      errorSpan.classList.add('show');
    }
    privacidad.parentElement.style.borderColor = '#b00020';
    return false;
  }
  
  const errorSpan = document.querySelector('.privacy-error');
  if (errorSpan) {
    errorSpan.classList.remove('show');
  }
  privacidad.parentElement.style.borderColor = '#e0e0e0';
  return true;
}

// Validar fuerzas armadas
function validarFuerzasArmadas() {
  if (!fuerzasArmadas.value) {
    mostrarError(fuerzasArmadas, "Seleccione una opción");
    return false;
  }
  limpiarError(fuerzasArmadas);
  return true;
}

// Validar tiene discapacidad
function validarTieneDiscapacidad() {
  if (!tieneDiscapacidad.value) {
    mostrarError(tieneDiscapacidad, "Seleccione una opción");
    return false;
  }
  limpiarError(tieneDiscapacidad);
  return true;
}

// Validar tipo de discapacidad (solo si tiene discapacidad = Sí)
function validarTipoDiscapacidad() {
  if (tieneDiscapacidad.value === "Si") {
    const valor = tipoDiscapacidad.value.trim();
    
    if (!valor) {
      mostrarError(tipoDiscapacidad, "Debe especificar qué discapacidad tiene");
      return false;
    }
    
    if (valor.length < 3) {
      mostrarError(tipoDiscapacidad, "Debe tener al menos 3 caracteres");
      return false;
    }
    
    limpiarError(tipoDiscapacidad);
    return true;
  }
  
  // Si no tiene discapacidad, el campo no es obligatorio
  return true;
}

// ===============================
// MOSTRAR/LIMPIAR ERRORES
// ===============================
function mostrarError(campo, mensaje) {
  campo.classList.add("input-error");
  campo.classList.remove("valid");
  
  // Buscar el span de error en el row padre
  const errorSpan = campo.parentElement.querySelector('.error-message');
  
  if (errorSpan) {
    errorSpan.textContent = mensaje;
    errorSpan.classList.add('show');
  }
}

function limpiarError(campo) {
  campo.classList.remove("input-error");
  campo.classList.add("valid");
  
  const errorSpan = campo.parentElement.querySelector('.error-message');
  if (errorSpan) {
    errorSpan.classList.remove('show');
  }
}

function limpiarTodosLosErrores() {
  const campos = form.querySelectorAll('input, select');
  campos.forEach(campo => {
    campo.classList.remove("input-error", "valid");
    const errorSpan = campo.parentElement.querySelector('.error-message');
    if (errorSpan) {
      errorSpan.classList.remove('show');
    }
  });
  
  // Limpiar error de privacidad
  const errorPriv = document.querySelector('.privacy-error');
  if (errorPriv) {
    errorPriv.classList.remove('show');
  }
  if (privacidad) {
    privacidad.parentElement.style.borderColor = '#e0e0e0';
  }
  
  // Resetear progreso
  actualizarProgreso();
}

// ===============================
// AJUSTES AUTOMÁTICOS
// ===============================

// Ajustar maxlength según tipo de documento
function ajustarTipoDocumento() {
  const tipo = tipoDoc.value;
  
  numDoc.value = '';
  
  if (tipo === 'DNI') {
    numDoc.maxLength = 8;
    numDoc.placeholder = 'Ingrese 8 dígitos del DNI';
  } else if (tipo === 'CE') {
    numDoc.maxLength = 9;
    numDoc.placeholder = 'Ingrese 9 dígitos del CE';
  }
  
  validarTipoDocumento();
}

// Limpiar solo números en documento
function limpiarSoloNumeros(campo) {
  campo.value = campo.value.replace(/[^0-9]/g, '');
}


// ✅ VERIFICAR DNI ÚNICO 
async function verificarDNIUnico(numeroDoc, tipoDoc) {
  try {
    const response = await fetch("/api/verificar-postulante", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        numero_documento: numeroDoc,
        tipo_documento: tipoDoc
      })
    });
    
    if (!response.ok) {
      throw new Error("Error al verificar el documento");
    }
    
    const result = await response.json();
    return result;
    
  } catch (error) {
    console.error("Error al verificar DNI:", error);
    throw error;
  }
}


// ===============================
// EVENT LISTENERS
// ===============================

// Área 
area.addEventListener('change', () => {
  validarArea();
  actualizarProgreso();
});
area.addEventListener('blur', validarArea);

// Convocatoria
convocatoria.addEventListener('change', () => {
  validarConvocatoria();
  actualizarProgreso();
});
convocatoria.addEventListener('blur', validarConvocatoria);

// ✅ APELLIDOS - TODO EN MAYÚSCULAS
apellidos.addEventListener('input', function() {
  // Permitir solo letras y espacios
  this.value = this.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
  // Convertir a mayúsculas
  this.value = this.value.toUpperCase();
  actualizarProgreso();
});
apellidos.addEventListener('blur', validarApellidos);

// ✅ NOMBRES - TODO EN MAYÚSCULAS
nombres.addEventListener('input', function() {
  // Permitir solo letras y espacios
  this.value = this.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
  // Convertir a mayúsculas
  this.value = this.value.toUpperCase();
  actualizarProgreso();
});
nombres.addEventListener('blur', validarNombres);

// Tipo de documento
tipoDoc.addEventListener('change', () => {
  ajustarTipoDocumento();
  actualizarProgreso();
});

// Número de documento
numDoc.addEventListener('input', function() {
  limpiarSoloNumeros(this);
  if (this.value.length === this.maxLength) {
    validarNumeroDocumento();
  }
  actualizarProgreso();
});
numDoc.addEventListener('blur', validarNumeroDocumento);

// Fecha de nacimiento
fechaNacimiento.addEventListener('change', () => {
  validarFechaNacimiento();
  actualizarProgreso();
});
fechaNacimiento.addEventListener('blur', validarFechaNacimiento);

// Sexo
sexo.addEventListener('change', () => {
  validarSexo();
  actualizarProgreso();
});
sexo.addEventListener('blur', validarSexo);

// Celular
celular.addEventListener('input', function() {
  limpiarSoloNumeros(this);
  
  // Validar en tiempo real
  if (this.value.length === 1 && this.value !== '9') {
    mostrarError(this, 'El celular debe empezar con 9');
  } else if (this.value.length === 9) {
    validarCelular();
  } else if (this.value.length > 0 && this.value.length < 9) {
    limpiarError(this);
  }
  
  actualizarProgreso();
});
celular.addEventListener('blur', validarCelular);

// Correo
correo.addEventListener('input', function() {
  // Convertir a minúsculas
  this.value = this.value.toLowerCase();
  actualizarProgreso();
});
correo.addEventListener('blur', validarCorreo);

// Fuerzas Armadas
fuerzasArmadas.addEventListener('change', () => {
  validarFuerzasArmadas();
  actualizarProgreso();
});
fuerzasArmadas.addEventListener('blur', validarFuerzasArmadas);

// Tiene Discapacidad
tieneDiscapacidad.addEventListener('change', function() {
  validarTieneDiscapacidad();
  
  // Mostrar u ocultar campo de tipo de discapacidad
  if (this.value === "Si") {
    rowTipoDiscapacidad.style.display = 'grid';
    tipoDiscapacidad.required = true;
  } else {
    rowTipoDiscapacidad.style.display = 'none';
    tipoDiscapacidad.required = false;
    tipoDiscapacidad.value = '';
    limpiarError(tipoDiscapacidad);
  }
  
  actualizarProgreso();
});
tieneDiscapacidad.addEventListener('blur', validarTieneDiscapacidad);

// Tipo de Discapacidad
tipoDiscapacidad.addEventListener('input', function() {
  // Capitalizar primera letra de cada palabra
  if (this.value) {
    this.value = this.value
      .toLowerCase()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
});
tipoDiscapacidad.addEventListener('blur', validarTipoDiscapacidad);

// Privacidad
privacidad.addEventListener('change', validarPrivacidad);

// Modal de política de privacidad
document.getElementById('linkPrivacidad').addEventListener('click', function(e) {
  e.preventDefault();
  alert('POLÍTICA DE PRIVACIDAD\n\nLa Municipalidad Metropolitana de Lima se compromete a proteger sus datos personales de acuerdo con la Ley N° 29733 - Ley de Protección de Datos Personales.\n\nSus datos serán utilizados únicamente para el proceso de selección CAS 2026 y no serán compartidos con terceros sin su consentimiento.\n\nPara más información, comuníquese con la Oficina General de Recursos Humanos.');
});


// ===============================
// ENVÍO DEL FORMULARIO CON VALIDACIÓN DE DNI ÚNICO
// ===============================

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  
  // ============  VALIDAR TODOS LOS CAMPOS ============
  const validaciones = [
    validarArea(),
    validarConvocatoria(),
    validarApellidos(), // ✅ ACTUALIZADO
    validarNombres(),   // ✅ ACTUALIZADO
    validarTipoDocumento(),
    validarNumeroDocumento(),
    validarFechaNacimiento(),
    validarSexo(),
    validarCelular(),
    validarCorreo(),
    validarFuerzasArmadas(),
    validarTieneDiscapacidad(),
    validarTipoDiscapacidad(),
    validarPrivacidad()
  ];
  
  const todosValidos = validaciones.every(v => v === true);
  
  if (!todosValidos) {
    setMsg("❌ Por favor, complete todos los campos correctamente", false);
    showToastError("Complete todos los campos correctamente");
    
    // Scroll al primer error
    const primerError = form.querySelector('.input-error');
    if (primerError) {
      primerError.scrollIntoView({ behavior: 'smooth', block: 'center' });
      primerError.focus();
    } else if (!privacidad.checked) {
      privacidad.parentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    return;
  }
  
  // Obtener datos para verificación
  const numeroDoc = numDoc.value.trim();
  const tipoDocVal = tipoDoc.value;
  
  try {
    // ============ VERIFICAR SI EL DNI YA ESTÁ REGISTRADO ============
    setMsg("⏳ Verificando documento...", true);
    btnSubmit.disabled = true;
    btnSubmit.classList.add("loading");
    
    const verificacion = await verificarDNIUnico(numeroDoc, tipoDocVal);
    
    if (verificacion.existe) {
      // ❌ POSTULANTE YA REGISTRADO
      numDoc.classList.add('input-error');
      const errorMsg = numDoc.parentElement.querySelector('.error-message');
      if (errorMsg) {
        errorMsg.textContent = 'Este documento ya está registrado';
        errorMsg.classList.add('show');
      }
      
      // Mensaje detallado en formato multilinea
      const mensajeError = `⚠️ POSTULANTE YA REGISTRADO\n\nEl ${tipoDocVal} ${numeroDoc} ya se encuentra registrado en:\n"${verificacion.convocatoria}"\n\nRecuerde: Cada postulante solo puede registrarse en UNA convocatoria.`;
      
      setMsg(mensajeError, false);
      showToastError(`El ${tipoDocVal} ${numeroDoc} ya está registrado en otra convocatoria`);
      
      // Scroll al campo de documento
      numDoc.scrollIntoView({ behavior: 'smooth', block: 'center' });
      numDoc.focus();
      
      // Rehabilitar botón
      btnSubmit.disabled = false;
      btnSubmit.classList.remove("loading");
      
      return; // ❌ DETENER EL ENVÍO
    }
    
    // ============ ✅ DNI NO REGISTRADO - PROCEDER CON EL REGISTRO ============
    setMsg("📤 Enviando postulación...", true);
    
    // Preparar datos
    const payload = Object.fromEntries(new FormData(form).entries());
    
    // Remover el campo privacidad del payload (solo es para validación)
    delete payload.privacidad;
    
    // Si no tiene discapacidad, eliminar el campo tipo_discapacidad del payload
    if (payload.tiene_discapacidad === "No") {
      delete payload.tipo_discapacidad;
    }
    
    const response = await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const text = await response.text();
    let result;

    try {
      result = JSON.parse(text);
    } catch {
      console.error("Respuesta NO JSON del servidor:", text);
      throw new Error("Error interno del servidor. Revise la consola.");
    }

    if (!response.ok) {
      throw new Error(result.error || "Error al guardar");
    }

    // ✅ ÉXITO
    form.reset();
    limpiarTodosLosErrores();
    setMsg("", true);
    showToastSuccess("✅ Registro exitoso. Su postulación ha sido recibida.");
    
    // Resetear el campo convocatoria después del reset
    convocatoria.disabled = true;
    convocatoria.innerHTML = '<option value="" selected disabled>Primero seleccione un área</option>';

  } catch (err) {
    console.error(err);
    setMsg("❌ " + err.message, false);
    showToastError(err.message);
  } finally {
    btnSubmit.disabled = false;
    btnSubmit.classList.remove("loading");
  }
});


// ===============================
// ACCESO ADMIN (3 CLICS EN LOGO)
// ===============================

const logoAdmin = document.getElementById("logoAdmin");

if (logoAdmin) {
  let clicks = 0;
  let timer = null;

  logoAdmin.addEventListener("click", () => {
    clicks++;

    clearTimeout(timer);
    timer = setTimeout(() => {
      clicks = 0;
    }, 1500);

    if (clicks === 3) {
      window.location.href = "/login";
    }
  });
}


// ===============================
// INICIALIZAR AL CARGAR
// ===============================
document.addEventListener('DOMContentLoaded', inicializar);