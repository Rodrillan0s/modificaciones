import React, { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL;

export default function AsistenteVoz({ setActiveMenu, userRolId }) {
  const [listening, setListening] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [supported, setSupported] = useState(true);

  // Web Speech API references
  let SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = "es-BO";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
  }

  useEffect(() => {
    if (!SpeechRecognition) {
      setSupported(false);
    }
  }, []);

  const hablar = (mensaje) => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(mensaje);
      utterance.lang = "es-ES";
      window.speechSynthesis.speak(utterance);
    }
  };

  const listar_reportes = () => {
    let reportesDisponibles = [];
    if ([1, 2, 4].includes(Number(userRolId))) {
      reportesDisponibles.push("Citas");
    }
    if (Number(userRolId) === 1) {
      reportesDisponibles.push("Pacientes", "Finanzas", "Inventario", "Administración");
    }
    const mensaje = `Los reportes disponibles para su nivel de acceso son: ${reportesDisponibles.join(", ")}.`;
    setStatusText(mensaje);
    hablar(mensaje);
  };

  const ejecutarEnvioVoz = async (modulo, destinatariosStr, isPrepareOnly = false, subtab = "resumen", fecha_desde = undefined, fecha_hasta = undefined, top = undefined, idProveedor = undefined, idMaterial = undefined) => {
    const modClean = modulo.toLowerCase().trim();
    let entidad = "";
    if (modClean.includes("cita")) {
      entidad = "citas";
    } else if (modClean.includes("finanza") || modClean.includes("financiero")) {
      entidad = "finanzas";
    } else if (modClean.includes("inventario")) {
      entidad = "inventario";
    } else if (modClean.includes("paciente")) {
      entidad = "pacientes";
    } else if (modClean.includes("administracion") || modClean.includes("administrativo")) {
      entidad = "administracion";
    } else {
      hablar(`No reconocí el reporte de ${modulo}.`);
      return;
    }

    setStatusText("Buscando destinatarios...");
    if (!isPrepareOnly) {
      hablar("Procesando envío de reporte.");
    }

    try {
      const resUsers = await fetch(`${API_URL}/reportes/disponibles/usuarios`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      const dataUsers = await resUsers.json();
      if (!dataUsers.success) {
        hablar("Error al obtener la lista de usuarios del sistema.");
        return;
      }
      const users = dataUsers.data;

      let emailList = [];
      let targetDesc = "";

      if (destinatariosStr) {
        const destLower = destinatariosStr.toLowerCase();
        if (destLower.includes("administrador") || destLower.includes("admin")) {
          const admins = users.filter(u => u.rol.toLowerCase().includes("admin") || u.rol.toLowerCase().includes("administrador"));
          emailList = admins.map(u => u.correo);
          targetDesc = "todos los administradores";
        } else if (destLower.includes("odontologo") || destLower.includes("dentista") || destLower.includes("doctor")) {
          const doctors = users.filter(u => u.rol.toLowerCase().includes("odontologo") || u.rol.toLowerCase().includes("odontólogo"));
          emailList = doctors.map(u => u.correo);
          targetDesc = "todos los odontólogos";
        } else {
          const matchUser = users.find(u => destLower.includes(u.nombre.toLowerCase()) || u.nombre.toLowerCase().includes(destLower));
          if (matchUser) {
            emailList = [matchUser.correo];
            targetDesc = matchUser.nombre;
          }
        }
      }

      // If no recipients found and it is NOT prepare only, send to all admins by default
      if (emailList.length === 0 && !isPrepareOnly) {
        const admins = users.filter(u => u.rol.toLowerCase().includes("admin") || u.rol.toLowerCase().includes("administrador"));
        emailList = admins.map(u => u.correo);
        targetDesc = "todos los administradores";
      }

      let menuName = "";
      if (entidad === "citas") menuName = "Reporte Citas";
      else if (entidad === "finanzas") menuName = "Reporte Finanzas";
      else if (entidad === "inventario") menuName = "Reporte Inventario";
      else if (entidad === "pacientes") menuName = "Reporte Pacientes";
      else if (entidad === "administracion") menuName = "Reporte Administración";

      if (isPrepareOnly) {
        const msg = `Configurando envío manual de ${entidad} ${targetDesc ? `para ${targetDesc}` : ""}.`;
        setStatusText(msg);
        hablar(msg);
        
        if (menuName) {
          setActiveMenu(menuName);
        }

        setTimeout(() => {
          // Dispatch load event to configure the report in background
          window.dispatchEvent(new CustomEvent("generar-reporte-voz", {
            detail: { modulo: entidad, subtab, fecha_desde, fecha_hasta, top, id_proveedor: idProveedor, id_material: idMaterial }
          }));

          // Dispatch configuration event to the mailing panel
          window.dispatchEvent(new CustomEvent("configurar-envio-voz", {
            detail: { modulo: entidad, destinatarios: emailList }
          }));
        }, 300);
        return;
      }

      if (emailList.length === 0) {
        hablar(`No pude identificar a los destinatarios para enviar el reporte.`);
        return;
      }

      const resSend = await fetch(`${API_URL}/reportes/programacion-correos/ejecutar-manual`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          entidad,
          para: emailList.join(", "),
          tipo: subtab,
          fecha_inicio: fecha_desde,
          fecha_fin: fecha_hasta,
          top: top,
          id_proveedor: idProveedor,
          id_material: idMaterial
        }),
      });
      const dataSend = await resSend.json();
      if (dataSend.success) {
        const msg = `Reporte de ${entidad} enviado con éxito a ${targetDesc}.`;
        setStatusText(msg);
        hablar(msg);
        
        if (menuName) {
          setActiveMenu(menuName);
        }

        setTimeout(() => {
          // Trigger report generation as well
          window.dispatchEvent(new CustomEvent("generar-reporte-voz", {
            detail: { modulo: entidad, subtab, fecha_desde, fecha_hasta, top, id_proveedor: idProveedor, id_material: idMaterial }
          }));
        }, 300);
      } else {
        hablar("Hubo un error al despachar el reporte.");
      }
    } catch (err) {
      console.error(err);
      hablar("Error de red al intentar enviar el reporte.");
    }
  };

  const iniciarReconocimiento = () => {
    if (!recognition) {
      setStatusText("Reconocimiento de voz no soportado en este navegador.");
      return;
    }

    setListening(true);
    setStatusText("Escuchando... Hable ahora");
    
    recognition.start();

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setStatusText(`Escuché: "${transcript}"`);
      
      const transcriptLower = transcript.toLowerCase();

      // Dynamic database lookup matching
      let idProveedor = undefined;
      let idMaterial = undefined;
      let modTarget = "";
      let subtabName = "resumen";

      try {
        const [resMat, resProv] = await Promise.all([
          fetch(`${API_URL}/materiales`, { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }),
          fetch(`${API_URL}/proveedores`, { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } })
        ]);
        const dataMat = await resMat.json();
        const dataProv = await resProv.json();
        
        if (dataProv.success && dataProv.data) {
          const matched = dataProv.data.find(p => transcriptLower.includes(p.nombre_proveedor.toLowerCase()));
          if (matched) {
            idProveedor = matched.id_proveedor || matched.id;
            modTarget = "inventario";
          }
        }
        if (dataMat.success && dataMat.data) {
          const matched = dataMat.data.find(m => transcriptLower.includes(m.nombre_material.toLowerCase()));
          if (matched) {
            idMaterial = matched.id_material || matched.id;
            modTarget = "inventario";
          }
        }
      } catch (err) {
        console.error("Error doing dynamic catalog match inside voice assistant:", err);
      }

      // 1. Detección de palabras clave para identificar el módulo y sub-pestaña
      if (transcriptLower.includes("cita") || transcriptLower.includes("agenda") || transcriptLower.includes("agendamiento")) {
        modTarget = "citas";
        if (transcriptLower.includes("global odontologos") || transcriptLower.includes("todos los odontologos") || transcriptLower.includes("todos los odontólogos")) {
          subtabName = "global_odontologos";
        } else if (transcriptLower.includes("global") || transcriptLower.includes("todos")) {
          subtabName = "global";
        } else if (transcriptLower.includes("paciente") || transcriptLower.includes("pacientes")) {
          subtabName = "pacientes";
        } else if (transcriptLower.includes("odontologo") || transcriptLower.includes("odontólogos")) {
          subtabName = "odontologos";
        }
      } else if (transcriptLower.includes("paciente") || transcriptLower.includes("cliente")) {
        modTarget = "pacientes";
        if (transcriptLower.includes("frecuente") || transcriptLower.includes("frecuentes") || transcriptLower.includes("visita") || transcriptLower.includes("visitas")) {
          subtabName = "frecuentes";
        } else if (transcriptLower.includes("aporte") || transcriptLower.includes("aportes") || transcriptLower.includes("mayor pago") || transcriptLower.includes("pagaron mas")) {
          subtabName = "aportes";
        } else if (transcriptLower.includes("deuda") || transcriptLower.includes("deudas") || transcriptLower.includes("deudor") || transcriptLower.includes("deudores") || transcriptLower.includes("pendiente")) {
          subtabName = "deudores";
        } else if (transcriptLower.includes("inactivo") || transcriptLower.includes("inactivos") || transcriptLower.includes("antiguo") || transcriptLower.includes("antiguos")) {
          subtabName = "inactivos";
        } else if (transcriptLower.includes("general") || transcriptLower.includes("historial")) {
          subtabName = "general";
        }
      } else if (transcriptLower.includes("finanza") || transcriptLower.includes("financiero") || transcriptLower.includes("dinero") || transcriptLower.includes("pago") || transcriptLower.includes("pagos") || transcriptLower.includes("caja") || transcriptLower.includes("ingreso") || transcriptLower.includes("ingresos") || transcriptLower.includes("gasto") || transcriptLower.includes("gastos") || transcriptLower.includes("ganancia") || transcriptLower.includes("ganancias")) {
        modTarget = "finanzas";
        if (transcriptLower.includes("mensual") || transcriptLower.includes("evolucion") || transcriptLower.includes("mes a mes")) {
          subtabName = "mensual";
        } else if (transcriptLower.includes("odontologo") || transcriptLower.includes("odontólogos") || transcriptLower.includes("dentista") || transcriptLower.includes("dentistas") || transcriptLower.includes("doctor") || transcriptLower.includes("doctores")) {
          subtabName = "odontologos";
        } else if (transcriptLower.includes("procedimiento") || transcriptLower.includes("procedimientos") || transcriptLower.includes("tratamiento") || transcriptLower.includes("tratamientos")) {
          subtabName = "procedimientos";
        } else if (transcriptLower.includes("metodo") || transcriptLower.includes("metodos") || transcriptLower.includes("tarjeta") || transcriptLower.includes("efectivo")) {
          subtabName = "metodos";
        } else if (transcriptLower.includes("saldo") || transcriptLower.includes("saldos") || transcriptLower.includes("amortizacion") || transcriptLower.includes("deuda") || transcriptLower.includes("deudas")) {
          subtabName = "saldos";
        }
      } else if (transcriptLower.includes("inventario") || transcriptLower.includes("material") || transcriptLower.includes("stock") || transcriptLower.includes("insumo") || transcriptLower.includes("insumos") || transcriptLower.includes("merma") || transcriptLower.includes("mermas") || transcriptLower.includes("perdida") || transcriptLower.includes("pérdida") || transcriptLower.includes("almacen") || transcriptLower.includes("vencer") || transcriptLower.includes("vencimiento") || transcriptLower.includes("vencimientos") || transcriptLower.includes("caducar") || transcriptLower.includes("proveedor") || transcriptLower.includes("proveedores")) {
        modTarget = "inventario";
        if (transcriptLower.includes("merma") || transcriptLower.includes("mermas") || transcriptLower.includes("perdida") || transcriptLower.includes("pérdida")) {
          subtabName = "mermas";
        } else if (transcriptLower.includes("ingreso") || transcriptLower.includes("ingresos") || transcriptLower.includes("entrada") || transcriptLower.includes("entradas")) {
          subtabName = "ingresos";
        } else if (transcriptLower.includes("vencer") || transcriptLower.includes("vencimiento") || transcriptLower.includes("vencimientos") || transcriptLower.includes("caducar")) {
          subtabName = "vencimientos";
        } else if (transcriptLower.includes("estatico") || transcriptLower.includes("fecha corte") || transcriptLower.includes("corte")) {
          subtabName = "estatico";
        } else {
          subtabName = "general";
        }
      } else if (transcriptLower.includes("administracion") || transcriptLower.includes("administrativo") || transcriptLower.includes("sala") || transcriptLower.includes("salas") || transcriptLower.includes("consultorio") || transcriptLower.includes("consultorios") || transcriptLower.includes("servicio") || transcriptLower.includes("servicios") || transcriptLower.includes("procedimiento") || transcriptLower.includes("procedimientos") || transcriptLower.includes("personal") || transcriptLower.includes("ocupada") || transcriptLower.includes("ocupadas")) {
        modTarget = "administracion";
        if (transcriptLower.includes("sala") || transcriptLower.includes("salas") || transcriptLower.includes("consultorio") || transcriptLower.includes("consultorios") || transcriptLower.includes("ocupada") || transcriptLower.includes("ocupadas")) {
          subtabName = "salas";
        } else if (transcriptLower.includes("servicio") || transcriptLower.includes("servicios")) {
          subtabName = "servicios";
        } else if (transcriptLower.includes("procedimiento") || transcriptLower.includes("procedimientos")) {
          subtabName = "procedimientos";
        } else if (transcriptLower.includes("personal") || transcriptLower.includes("apoyo")) {
          subtabName = "personal";
        }
      }

      // 2. Determinar si solicita envío o preparación por correo
      const isPrepare = transcriptLower.includes("prepara") || transcriptLower.includes("preparar") || transcriptLower.includes("configura") || transcriptLower.includes("configurar");
      const isSend = transcriptLower.includes("envia") || transcriptLower.includes("enviar") || transcriptLower.includes("manda") || transcriptLower.includes("mandar") || transcriptLower.includes("correo") || transcriptLower.includes("mail");

      // Parse dates y top N para inyección
      let fecha_desde = undefined;
      let fecha_hasta = undefined;
      const now = new Date();

      if (transcriptLower.includes("este mes")) {
        const y = now.getFullYear();
        const m = now.getMonth();
        const first = new Date(y, m, 1);
        const last = new Date(y, m + 1, 0);
        fecha_desde = first.toISOString().split('T')[0];
        fecha_hasta = last.toISOString().split('T')[0];
      } else if (transcriptLower.includes("mes pasado") || transcriptLower.includes("el mes pasado")) {
        const y = now.getFullYear();
        const m = now.getMonth();
        const first = new Date(y, m - 1, 1);
        const last = new Date(y, m, 0);
        fecha_desde = first.toISOString().split('T')[0];
        fecha_hasta = last.toISOString().split('T')[0];
      } else if (transcriptLower.includes("esta semana")) {
        const currentDay = now.getDay();
        const distanceToMonday = currentDay === 0 ? -6 : 1 - currentDay;
        const monday = new Date(now);
        monday.setDate(now.getDate() + distanceToMonday);
        const sunday = new Date(monday);
        sunday.setDate(monday.getDate() + 6);
        fecha_desde = monday.toISOString().split('T')[0];
        fecha_hasta = sunday.toISOString().split('T')[0];
      } else if (transcriptLower.includes("hoy")) {
        fecha_desde = now.toISOString().split('T')[0];
        fecha_hasta = now.toISOString().split('T')[0];
      } else if (transcriptLower.includes("este año")) {
        fecha_desde = `${now.getFullYear()}-01-01`;
        fecha_hasta = `${now.getFullYear()}-12-31`;
      }

      let topN = undefined;
      const matchTop = transcriptLower.match(/(?:primeros|top|limite|límite|primeras)\s+(\d+)/) || transcriptLower.match(/(\d+)\s+(?:primeros|lotes|insumos|materiales|primeras)/);
      if (matchTop && matchTop[1]) {
        topN = parseInt(matchTop[1]);
      }

      // Si solicita envío/preparación Y tenemos módulo identificado:
      if ((isPrepare || isSend) && modTarget) {
        let dest = "";
        if (transcriptLower.includes("administrador") || transcriptLower.includes("admin")) {
          dest = "administradores";
        } else if (transcriptLower.includes("odontologo") || transcriptLower.includes("doctor") || transcriptLower.includes("dentista")) {
          dest = "odontologos";
        } else {
          const matchA = transcriptLower.match(/(?:a|para)\s+([a-zA-Z\s\d\.\@\-_]+)/);
          if (matchA && matchA[1]) {
            dest = matchA[1].trim();
          }
        }
        
        // Ejecutamos flujo de envío/preparación (isPrepareOnly = isPrepare || dest es vacío)
        ejecutarEnvioVoz(modTarget, dest, isPrepare || !dest, subtabName, fecha_desde, fecha_hasta, topN, idProveedor, idMaterial);
        return;
      }

      // 3. Si solo solicita visualizar/generar un reporte
      if (modTarget) {
        let menuTarget = null;
        let spokenResponse = "";

        if (modTarget === "citas") {
          if ([1, 2, 4].includes(Number(userRolId))) {
            menuTarget = "Reporte Citas";
            spokenResponse = `Generando reporte de citas: ${subtabName}`;
          } else {
            spokenResponse = "No tiene permisos para acceder al reporte de citas";
          }
        } else if (modTarget === "pacientes") {
          if (Number(userRolId) === 1) {
            menuTarget = "Reporte Pacientes";
            spokenResponse = `Generando reporte de pacientes: ${subtabName}`;
          } else {
            spokenResponse = "Acceso denegado al reporte de pacientes";
          }
        } else if (modTarget === "finanzas") {
          if (Number(userRolId) === 1) {
            menuTarget = "Reporte Finanzas";
            spokenResponse = `Generando reporte financiero: ${subtabName}`;
          } else {
            spokenResponse = "Acceso denegado al reporte financiero";
          }
        } else if (modTarget === "inventario") {
          if (Number(userRolId) === 1) {
            menuTarget = "Reporte Inventario";
            spokenResponse = `Generando reporte de inventario: ${subtabName}`;
          } else {
            spokenResponse = "Acceso denegado al reporte de inventario";
          }
        } else if (modTarget === "administracion") {
          if (Number(userRolId) === 1) {
            menuTarget = "Reporte Administración";
            spokenResponse = `Generando reporte de ${subtabName}`;
          } else {
            spokenResponse = "Acceso denegado al reporte administrativo";
          }
        }

        if (menuTarget) {
          setStatusText(spokenResponse);
          hablar(spokenResponse);
          setActiveMenu(menuTarget);
          setTimeout(() => {
            window.dispatchEvent(new CustomEvent("generar-reporte-voz", { 
              detail: { modulo: modTarget, subtab: subtabName, fecha_desde, fecha_hasta, top: topN, id_proveedor: idProveedor, id_material: idMaterial } 
            }));
          }, 300);
        } else if (spokenResponse) {
          setStatusText(spokenResponse);
          hablar(spokenResponse);
        }
        return;
      }

      if (transcriptLower.includes("listar reportes") || transcriptLower.includes("qué reportes") || transcriptLower.includes("que reportes") || transcriptLower.includes("ayuda")) {
        listar_reportes();
        return;
      }

      hablar("No reconocí el comando. Diga por ejemplo: Mostrar reporte de inventario, o preparar reporte de finanzas.");
    };

    recognition.onerror = (event) => {
      console.error(event.error);
      setStatusText(`Error de voz: ${event.error}`);
      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
    };
  };

  if (!supported) {
    return null;
  }

  return (
    <div className="flex flex-col items-end gap-2 text-xs font-semibold print:hidden">
      <div className="flex items-center gap-2">
        {statusText && (
          <span className="text-[10px] text-gray-400 bg-gray-50 px-3 py-1.5 rounded-xl border border-gray-100 max-w-xs truncate">
            {statusText}
          </span>
        )}
        <button
          type="button"
          onClick={iniciarReconocimiento}
          disabled={listening}
          className={`px-4 py-2 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all border shadow-sm cursor-pointer ${
            listening
              ? "bg-red-50 text-red-500 border-red-200 animate-pulse"
              : "bg-emerald-50 text-[#148F77] border-emerald-100 hover:bg-emerald-100"
          }`}
        >
          {listening ? "Escuchando..." : "Comando por Voz"}
        </button>
      </div>
    </div>
  );
}
