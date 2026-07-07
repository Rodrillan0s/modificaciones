import React, { useState, useEffect } from "react";

export default function ModalEnviarCorreo({ isOpen, onClose, modulo, subtab, fechaInicio, fechaFin, top, idProveedor, idMaterial, prefilledEmails }) {
  const [usuarios, setUsuarios] = useState([]);
  const [destinatarios, setDestinatarios] = useState([]);
  const [customEmails, setCustomEmails] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: "", type: "" });
  const API_URL = import.meta.env.VITE_API_URL;

  useEffect(() => {
    if (isOpen) {
      fetchUsuarios();
      setMessage({ text: "", type: "" });
      setDestinatarios(prefilledEmails || []);
      setCustomEmails("");
    }
  }, [isOpen, prefilledEmails]);

  const fetchUsuarios = async () => {
    try {
      const res = await fetch(`${API_URL}/reportes/disponibles/usuarios`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      const data = await res.json();
      if (data.success) {
        setUsuarios(data.data || []);
      }
    } catch (err) {
      console.error("Error al obtener usuarios en modal de envío", err);
    }
  };

  const handleCheckboxChange = (correo) => {
    if (destinatarios.includes(correo)) {
      setDestinatarios(destinatarios.filter(c => c !== correo));
    } else {
      setDestinatarios([...destinatarios, correo]);
    }
  };

  const selectAllAdmins = () => {
    const adminEmails = usuarios
      .filter(u => u.rol.toLowerCase().includes("admin") || u.rol.toLowerCase().includes("administrador"))
      .map(u => u.correo);
    setDestinatarios(adminEmails);
  };

  const selectAllOdontologos = () => {
    const docEmails = usuarios
      .filter(u => u.rol.toLowerCase().includes("odontologo") || u.rol.toLowerCase().includes("odontólogo"))
      .map(u => u.correo);
    setDestinatarios(docEmails);
  };

  const handleSend = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ text: "", type: "" });

    let finalEmails = [...destinatarios];
    if (customEmails.trim()) {
      const parsed = customEmails.split(",").map(e => e.trim()).filter(Boolean);
      finalEmails = [...new Set([...finalEmails, ...parsed])];
    }

    if (finalEmails.length === 0) {
      setMessage({ text: "Debe seleccionar o escribir al menos un destinatario", type: "error" });
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_URL}/reportes/programacion-correos/ejecutar-manual`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({
          entidad: modulo,
          para: finalEmails.join(", "),
          tipo: subtab,
          fecha_inicio: fechaInicio,
          fecha_fin: fechaFin,
          top: top,
          id_proveedor: idProveedor,
          id_material: idMaterial
        })
      });
      const data = await res.json();
      if (data.success) {
        setMessage({ text: "Reporte enviado exitosamente por correo electrónico", type: "success" });
        setTimeout(() => {
          onClose();
        }, 1500);
      } else {
        setMessage({ text: data.message || "Error al enviar el reporte", type: "error" });
      }
    } catch (err) {
      setMessage({ text: "Error de conexión al servidor", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm print:hidden">
      <div className="relative w-full max-w-lg p-6 bg-white rounded-2xl shadow-xl border border-gray-100 m-4 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex justify-between items-center pb-4 border-b border-gray-100 mb-4">
          <div>
            <h3 className="text-base font-black text-[#2A5C4D]">Enviar Reporte por Correo</h3>
            <p className="text-[10px] text-gray-400 mt-0.5">Módulo: {modulo.toUpperCase()} • Sub-tipo: {subtab}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 font-bold text-lg">&times;</button>
        </div>

        {message.text && (
          <div className={`p-3 rounded-xl text-xs font-bold mb-4 ${
            message.type === "success" ? "bg-emerald-50 text-emerald-600 border border-emerald-100" : "bg-red-50 text-red-500 border border-red-100"
          }`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSend} className="space-y-4">
          {/* Quick Select Buttons */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectAllAdmins}
              className="px-3 py-1.5 rounded-lg bg-emerald-50 text-[#148F77] border border-emerald-100 text-[10px] font-black hover:bg-emerald-100 transition-all"
            >
              Seleccionar Administradores
            </button>
            {modulo === "citas" && (
              <button
                type="button"
                onClick={selectAllOdontologos}
                className="px-3 py-1.5 rounded-lg bg-emerald-50 text-[#148F77] border border-emerald-100 text-[10px] font-black hover:bg-emerald-100 transition-all"
              >
                Seleccionar Odontólogos
              </button>
            )}
          </div>

          {/* User Checkbox List */}
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-[#2A5C4D] uppercase tracking-wider block">
              Lista de Usuarios del Sistema
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-y-auto p-3 bg-gray-50/50 rounded-xl border border-gray-100">
              {usuarios
                .filter((u) => {
                  if (["inventario", "finanzas", "administracion", "pacientes"].includes(modulo)) {
                    return u.rol.toUpperCase() === "ADMINISTRADOR";
                  }
                  return u.rol.toUpperCase() === "ADMINISTRADOR" || u.rol.toUpperCase() === "ODONTOLOGO";
                })
                .map((u) => (
                  <label key={u.id_usuario} className="flex items-center gap-2 cursor-pointer p-1 hover:bg-white rounded transition-colors">
                    <input
                      type="checkbox"
                      checked={destinatarios.includes(u.correo)}
                      onChange={() => handleCheckboxChange(u.correo)}
                      className="rounded text-[#148F77] focus:ring-[#148F77] border-gray-200"
                    />
                    <div className="min-w-0">
                      <p className="text-[10px] font-bold text-[#2A5C4D] truncate">{u.nombre}</p>
                      <p className="text-[8px] text-gray-400 truncate">{u.correo}</p>
                    </div>
                  </label>
                ))}
              {usuarios.length === 0 && (
                <p className="text-[9px] text-gray-400 col-span-2">Cargando usuarios...</p>
              )}
            </div>
          </div>

          {/* Custom Emails */}
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-[#2A5C4D] uppercase tracking-wider block">
              Correos Externos Adicionales (separados por comas)
            </label>
            <input
              type="text"
              placeholder="ejemplo@correo.com, auditor@correo.com"
              value={customEmails}
              onChange={(e) => setCustomEmails(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-gray-100 bg-gray-50/50 text-xs placeholder-gray-300 focus:outline-none focus:border-[#148F77]"
            />
          </div>

          {/* Footer Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-bold text-gray-500 hover:bg-gray-50 rounded-xl transition-all"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 bg-[#148F77] hover:bg-[#117A65] text-white text-xs font-black rounded-xl shadow-sm transition-all disabled:opacity-50"
            >
              {loading ? "Enviando..." : "Enviar Correo"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
