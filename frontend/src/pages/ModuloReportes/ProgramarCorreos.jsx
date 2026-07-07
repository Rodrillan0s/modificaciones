import { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL;

export default function ProgramarCorreos({ user }) {
  const [usuarios, setUsuarios] = useState([]);
  const [programaciones, setProgramaciones] = useState([]);
  
  // Form Programación Automática
  const [modulo, setModulo] = useState("citas");
  const [destinatariosSeleccionados, setDestinatariosSeleccionados] = useState([]);
  const [customEmails, setCustomEmails] = useState("");
  const [frecuencia, setFrecuencia] = useState("diario");
  const [habilitado, setHabilitado] = useState(true);

  // Form Envío Manual
  const [moduloManual, setModuloManual] = useState("citas");
  const [destinatariosManual, setDestinatariosManual] = useState([]);
  const [customEmailsManual, setCustomEmailsManual] = useState("");
  const [tipoManual, setTipoManual] = useState("general");
  const [fechaInicioManual, setFechaInicioManual] = useState("");
  const [fechaFinManual, setFechaFinManual] = useState("");
  const [topManual, setTopManual] = useState("");

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: "", type: "" });

  useEffect(() => {
    fetchUsuarios();
    fetchProgramaciones();
  }, []);

  useEffect(() => {
    const handleVoiceConfig = (e) => {
      if (e.detail.modulo) {
        setModuloManual(e.detail.modulo);
      }
      if (e.detail.destinatarios) {
        setDestinatariosManual(e.detail.destinatarios);
      }
      if (e.detail.subtab) {
        setTipoManual(e.detail.subtab);
      }
      if (e.detail.fecha_desde) {
        setFechaInicioManual(e.detail.fecha_desde);
      }
      if (e.detail.fecha_hasta) {
        setFechaFinManual(e.detail.fecha_hasta);
      }
      if (e.detail.top) {
        setTopManual(e.detail.top);
      }
    };
    window.addEventListener("configurar-envio-voz", handleVoiceConfig);
    return () => window.removeEventListener("configurar-envio-voz", handleVoiceConfig);
  }, []);

  useEffect(() => {
    if (moduloManual === "citas") {
      setTipoManual("global");
    } else if (moduloManual === "finanzas") {
      setTipoManual("resumen");
    } else if (moduloManual === "inventario") {
      setTipoManual("general");
    } else if (moduloManual === "pacientes") {
      setTipoManual("resumen");
    } else if (moduloManual === "administracion") {
      setTipoManual("salas");
    }
    setFechaInicioManual("");
    setFechaFinManual("");
    setTopManual("");
  }, [moduloManual]);

  const fetchUsuarios = async () => {
    try {
      const res = await fetch(`${API_URL}/reportes/disponibles/usuarios`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      const data = await res.json();
      if (data.success) {
        setUsuarios(data.data);
      }
    } catch (err) {
      console.error("Error al obtener usuarios:", err);
    }
  };

  const fetchProgramaciones = async () => {
    try {
      const res = await fetch(`${API_URL}/reportes/programacion-correos`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      const data = await res.json();
      if (data.success) {
        setProgramaciones(data.data);
      }
    } catch (err) {
      console.error("Error al obtener programaciones:", err);
    }
  };

  const handleCheckboxChange = (email, mode = "auto") => {
    if (mode === "auto") {
      setDestinatariosSeleccionados((prev) =>
        prev.includes(email) ? prev.filter((e) => e !== email) : [...prev, email]
      );
    } else {
      setDestinatariosManual((prev) =>
        prev.includes(email) ? prev.filter((e) => e !== email) : [...prev, email]
      );
    }
  };

  const handleProgramar = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ text: "", type: "" });

    let finalEmails = [...destinatariosSeleccionados];
    if (customEmails.trim()) {
      const parsed = customEmails.split(",").map((email) => email.trim()).filter((email) => email);
      finalEmails = [...new Set([...finalEmails, ...parsed])];
    }

    if (finalEmails.length === 0) {
      setMessage({ text: "Debe seleccionar o escribir al menos un destinatario", type: "error" });
      setLoading(false);
      return;
    }

    const tarea = `Envio Automatico de ${modulo.charAt(0).toUpperCase() + modulo.slice(1)}`;

    try {
      const res = await fetch(`${API_URL}/reportes/programacion-correos`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          tarea,
          entidad: modulo,
          categoria: frecuencia,
          para: finalEmails.join(", "),
          habilitado,
        }),
      });

      const data = await res.json();
      if (data.success) {
        setMessage({ text: "Programación guardada exitosamente", type: "success" });
        fetchProgramaciones();
        setDestinatariosSeleccionados([]);
        setCustomEmails("");
      } else {
        setMessage({ text: data.message || "Error al guardar programación", type: "error" });
      }
    } catch (err) {
      setMessage({ text: "Error de red al conectar con el servidor", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleEnviarManual = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ text: "", type: "" });

    let finalEmails = [...destinatariosManual];
    if (customEmailsManual.trim()) {
      const parsed = customEmailsManual.split(",").map((email) => email.trim()).filter((email) => email);
      finalEmails = [...new Set([...finalEmails, ...parsed])];
    }

    if (finalEmails.length === 0) {
      setMessage({ text: "Debe seleccionar o escribir al menos un destinatario para el envío manual", type: "error" });
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_URL}/reportes/programacion-correos/ejecutar-manual`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          entidad: moduloManual,
          para: finalEmails.join(", "),
          tipo: tipoManual,
          fecha_inicio: fechaInicioManual,
          fecha_fin: fechaFinManual,
          top: topManual || undefined,
        }),
      });

      const data = await res.json();
      if (data.success) {
        setMessage({ text: `Reporte de ${moduloManual} enviado exitosamente por correo`, type: "success" });
        setDestinatariosManual([]);
        setCustomEmailsManual("");
      } else {
        setMessage({ text: data.message || "Error al enviar el reporte manual", type: "error" });
      }
    } catch (err) {
      setMessage({ text: "Error de red al conectar con el servidor", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const usuariosFiltrados = usuarios.filter((u) => {
    if (modulo === "citas") {
      return u.rol.toUpperCase() === "ODONTOLOGO";
    } else {
      return u.rol.toUpperCase() === "ADMINISTRADOR";
    }
  });

  const usuariosFiltradosManual = usuarios.filter((u) => {
    if (moduloManual === "citas") {
      return u.rol.toUpperCase() === "ODONTOLOGO";
    } else {
      return u.rol.toUpperCase() === "ADMINISTRADOR";
    }
  });

  const handleSelectAllAuto = () => {
    const filteredEmails = usuariosFiltrados.map(u => u.correo);
    const allSelected = filteredEmails.every(e => destinatariosSeleccionados.includes(e));
    if (allSelected) {
      setDestinatariosSeleccionados(prev => prev.filter(e => !filteredEmails.includes(e)));
    } else {
      setDestinatariosSeleccionados(prev => [...new Set([...prev, ...filteredEmails])]);
    }
  };

  const handleSelectAllManual = () => {
    const filteredEmails = usuariosFiltradosManual.map(u => u.correo);
    const allSelected = filteredEmails.every(e => destinatariosManual.includes(e));
    if (allSelected) {
      setDestinatariosManual(prev => prev.filter(e => !filteredEmails.includes(e)));
    } else {
      setDestinatariosManual(prev => [...new Set([...prev, ...filteredEmails])]);
    }
  };

  return (
    <div className="flex flex-col bg-white rounded-3xl shadow-sm border border-emerald-50 relative overflow-hidden w-full">
      
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-6 lg:p-8 border-b border-gray-50 bg-gray-50/30">
        <div>
          <h2 className="text-2xl font-black text-[#2A5C4D]">Programar Correos Automáticos</h2>
          <p className="text-xs text-gray-400 mt-1 font-medium tracking-wide">
            Configure la frecuencia de envíos automáticos o realice despachos manuales inmediatos de reportes.
          </p>
        </div>
      </div>

      {/* CONTENIDO PRINCIPAL */}
      <div className="p-6 lg:p-8 space-y-8">
        
        {/* MENSAJES DE RETROALIMENTACIÓN */}
        {message.text && (
          <div
            className={`p-4 rounded-xl border text-sm font-bold flex items-center gap-3 transition-all ${
              message.type === "success"
                ? "bg-emerald-50 text-emerald-700 border-emerald-100"
                : "bg-red-50 text-red-700 border-red-100"
            }`}
          >
            <span className="text-lg">
              {message.type === "success" ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              )}
            </span>
            <p>{message.text}</p>
          </div>
        )}

        {/* FORMS GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* COLUMNA 1: FORM PROGRAMAR AUTOMÁTICO */}
          <div className="p-6 rounded-2xl border border-gray-100 space-y-6 bg-white shadow-sm">
            <div>
              <h3 className="text-md font-black text-[#2A5C4D] tracking-tight">Programar Envío Recurrente</h3>
              <p className="text-xs text-gray-400">Configure los destinatarios y la frecuencia de notificaciones.</p>
            </div>

            <form onSubmit={handleProgramar} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-[#2A5C4D] uppercase tracking-wider block">
                    Reporte / Módulo
                  </label>
                  <select
                    value={modulo}
                    onChange={(e) => setModulo(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-100 bg-gray-50/50 text-[#2A5C4D] font-bold text-xs focus:outline-none focus:border-[#148F77]"
                  >
                    <option value="citas">Citas (Recordatorio)</option>
                    <option value="finanzas">Finanzas (Reporte General)</option>
                    <option value="inventario">Inventario (Insumos y Stock)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-[#2A5C4D] uppercase tracking-wider block">
                    Frecuencia
                  </label>
                  <select
                    value={frecuencia}
                    onChange={(e) => setFrecuencia(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-100 bg-gray-50/50 text-[#2A5C4D] font-bold text-xs focus:outline-none focus:border-[#148F77]"
                  >
                    <option value="diario">Diario</option>
                    <option value="semanal">Semanal</option>
                    <option value="mensual">Mensual</option>
                  </select>
                </div>

              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center mb-1">
                  <label className="text-[10px] font-bold text-[#2A5C4D] uppercase tracking-wider block">
                    Destinatarios Habilitados
                  </label>
                  {usuariosFiltrados.length > 0 && (
                    <button
                      type="button"
                      onClick={handleSelectAllAuto}
                      className="text-[10px] text-[#148F77] hover:underline font-bold focus:outline-none"
                    >
                      {usuariosFiltrados.every(u => destinatariosSeleccionados.includes(u.correo)) ? "Desmarcar todos" : "Seleccionar todos"}
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-y-auto p-3 bg-gray-50/50 rounded-xl border border-gray-100">
                  {usuariosFiltrados.map((u) => (
                    <label key={`auto-${u.id_usuario}`} className="flex items-center gap-2.5 cursor-pointer p-1.5 hover:bg-white rounded-lg transition-colors">
                      <input
                        type="checkbox"
                        checked={destinatariosSeleccionados.includes(u.correo)}
                        onChange={() => handleCheckboxChange(u.correo, "auto")}
                        className="rounded text-[#148F77] focus:ring-[#148F77] border-gray-200"
                      />
                      <div className="min-w-0">
                        <p className="text-[11px] font-bold text-[#2A5C4D] truncate">{u.nombre}</p>
                        <p className="text-[9px] text-gray-400 truncate">{u.correo}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-[#2A5C4D] uppercase tracking-wider block">
                  Correos Adicionales (separados por coma)
                </label>
                <input
                  type="text"
                  placeholder="ejemplo@correo.com, auditor@correo.com"
                  value={customEmails}
                  onChange={(e) => setCustomEmails(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-100 bg-gray-50/50 text-xs placeholder-gray-300 focus:outline-none focus:border-[#148F77]"
                />
              </div>

              <div className="flex items-center gap-2 py-1">
                <input
                  type="checkbox"
                  id="habilitado"
                  checked={habilitado}
                  onChange={(e) => setHabilitado(e.target.checked)}
                  className="rounded text-[#148F77] focus:ring-[#148F77] border-gray-200"
                />
                <label htmlFor="habilitado" className="text-[11px] font-bold text-[#2A5C4D] cursor-pointer">
                  Activar programación automática
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-[#148F77] hover:bg-[#117A65] text-white font-black text-xs uppercase tracking-wider transition-all disabled:opacity-50"
              >
                {loading ? "Procesando..." : "Programar Envío"}
              </button>
            </form>
          </div>

          {/* COLUMNA 2: FORM ENVIAR MANUAL INMEDIATO */}
          <div className="p-6 rounded-2xl border border-gray-100 space-y-6 bg-white shadow-sm">
            <div>
              <h3 className="text-md font-black text-[#2A5C4D] tracking-tight">Envío Manual e Inmediato</h3>
              <p className="text-xs text-gray-400">Genera y despacha el reporte en tiempo real al correo indicado.</p>
            </div>

            <form onSubmit={handleEnviarManual} className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-[#2A5C4D] uppercase tracking-wider block">
                  Seleccionar Reporte
                </label>
                <select
                  value={moduloManual}
                  onChange={(e) => {
                    const val = e.target.value;
                    setModuloManual(val);
                    if (val === "citas") setTipoManual("global");
                    else if (val === "finanzas") setTipoManual("resumen");
                    else if (val === "inventario") setTipoManual("general");
                    else if (val === "pacientes") setTipoManual("resumen");
                    else if (val === "administracion") setTipoManual("salas");
                  }}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-100 bg-gray-50/50 text-[#2A5C4D] font-bold text-xs focus:outline-none focus:border-[#148F77]"
                >
                  <option value="citas">Citas (Recordatorio y Agenda)</option>
                  <option value="finanzas">Finanzas (Ingresos y Caja)</option>
                  <option value="inventario">Inventario (Insumos y Lotes)</option>
                  <option value="pacientes">Pacientes (Historial y Frecuencia)</option>
                  <option value="administracion">Administración (Salas y Servicios)</option>
                </select>
              </div>



              <div className="space-y-2">
                <div className="flex justify-between items-center mb-1">
                  <label className="text-[10px] font-bold text-[#2A5C4D] uppercase tracking-wider block">
                    Destinatarios
                  </label>
                  {usuariosFiltradosManual.length > 0 && (
                    <button
                      type="button"
                      onClick={handleSelectAllManual}
                      className="text-[10px] text-[#148F77] hover:underline font-bold focus:outline-none"
                    >
                      {usuariosFiltradosManual.every(u => destinatariosManual.includes(u.correo)) ? "Desmarcar todos" : "Seleccionar todos"}
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-y-auto p-3 bg-gray-50/50 rounded-xl border border-gray-100">
                  {usuariosFiltradosManual.map((u) => (
                    <label key={`manual-${u.id_usuario}`} className="flex items-center gap-2.5 cursor-pointer p-1.5 hover:bg-white rounded-lg transition-colors">
                      <input
                        type="checkbox"
                        checked={destinatariosManual.includes(u.correo)}
                        onChange={() => handleCheckboxChange(u.correo, "manual")}
                        className="rounded text-[#148F77] focus:ring-[#148F77] border-gray-200"
                      />
                      <div className="min-w-0">
                        <p className="text-[11px] font-bold text-[#2A5C4D] truncate">{u.nombre}</p>
                        <p className="text-[9px] text-gray-400 truncate">{u.correo}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-[#2A5C4D] uppercase tracking-wider block">
                  Correos Adicionales (separados por coma)
                </label>
                <input
                  type="text"
                  placeholder="ejemplo@correo.com, auditor@correo.com"
                  value={customEmailsManual}
                  onChange={(e) => setCustomEmailsManual(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-100 bg-gray-50/50 text-xs placeholder-gray-300 focus:outline-none focus:border-[#148F77]"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-black text-xs uppercase tracking-wider transition-all disabled:opacity-50"
              >
                {loading ? "Enviando..." : "Despachar Ahora"}
              </button>
            </form>
          </div>

        </div>

        {/* TAREAS PROGRAMADAS ACTIVAS (RESPONSIVE TABLE) */}
        <div className="p-6 rounded-2xl border border-gray-100 bg-white shadow-sm space-y-4">
          <div>
            <h3 className="text-md font-black text-[#2A5C4D] tracking-tight">Tareas Programadas en el Sistema</h3>
            <p className="text-xs text-gray-400">Resumen y estado de las configuraciones de envío automatizado.</p>
          </div>

          <div className="overflow-x-auto w-full">
            <table className="min-w-full divide-y divide-gray-100 text-left text-xs">
              <thead>
                <tr className="bg-gray-50/70 text-[#2A5C4D] font-black uppercase tracking-wider">
                  <th className="px-4 py-3 rounded-l-xl">Tarea</th>
                  <th className="px-4 py-3">Módulo</th>
                  <th className="px-4 py-3">Frecuencia</th>
                  <th className="px-4 py-3">Destinatarios</th>
                  <th className="px-4 py-3 rounded-r-xl">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {programaciones.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-4 py-6 text-center text-gray-400 italic">
                      No hay tareas automáticas configuradas actualmente.
                    </td>
                  </tr>
                ) : (
                  programaciones.map((p, idx) => (
                    <tr key={idx} className="hover:bg-gray-50/30 transition-colors">
                      <td className="px-4 py-3 font-bold text-[#2A5C4D]">{p.tarea}</td>
                      <td className="px-4 py-3 font-medium text-gray-600 capitalize">{p.entidad}</td>
                      <td className="px-4 py-3 font-medium text-gray-600 capitalize">{p.categoria}</td>
                      <td className="px-4 py-3 font-medium text-gray-500 max-w-xs truncate" title={p.para}>
                        {p.para}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block text-[9px] font-black uppercase px-2.5 py-0.5 rounded-full ${
                            p.habilitado
                              ? "bg-emerald-50 text-emerald-700"
                              : "bg-red-50 text-red-700"
                          }`}
                        >
                          {p.habilitado ? "Habilitado" : "Deshabilitado"}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
