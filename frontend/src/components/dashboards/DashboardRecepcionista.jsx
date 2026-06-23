import { useState, useEffect } from "react";
import {
  ESTADO_CITA,
  ESTADO_CITA_LABELS,
  ESTADO_CITA_COLORS,
} from "../../constants/enums";

const API_URL = import.meta.env.VITE_API_URL;

export default function DashboardRecepcionista({ user, dataMaster, setView, openModal }) {
  const [loading, setLoading] = useState(true);
  const [citasHoy, setCitasHoy] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCitasHoy = async () => {
      setLoading(true);
      setError(null);
      try {
        const todayStr = new Date().toISOString().split("T")[0];
        const headers = {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        };

        const res = await fetch(
          `${API_URL}/citas?page=1&limit=100&fecha_agen_desde=${todayStr}&fecha_agen_hasta=${todayStr}`,
          { headers }
        );
        const data = await res.json();

        if (data.success !== false) {
          setCitasHoy(data.data || []);
        } else {
          setError(data.message || "Error al cargar la agenda de hoy.");
        }
      } catch (err) {
        console.error("Error fetching receptionist stats:", err);
        setError("Error de conexión al cargar las citas de hoy.");
      } finally {
        setLoading(false);
      }
    };

    fetchCitasHoy();
  }, []);

  const getPacienteName = (id) => {
    if (!dataMaster?.pacientes) return id;
    const paciente = dataMaster.pacientes.find(
      (p) => (p.id_persona || p.id_usuario || p.id) == id
    );
    return paciente ? paciente.nombre : `Paciente #${id}`;
  };

  const getOdontologoName = (id) => {
    if (!dataMaster?.odontologos) return id;
    const odon = dataMaster.odontologos.find(
      (o) => (o.id_personal || o.id_persona || o.id) == id
    );
    return odon ? odon.nombre : `Doc. #${id}`;
  };

  const getSalaName = (id) => {
    if (!dataMaster?.salas) return `Sala #${id}`;
    const sala = dataMaster.salas.find((s) => s.id_sala == id);
    return sala ? sala.nombre : `Sala #${id}`;
  };

  const formatTime = (dateString) => {
    if (!dateString) return "";
    if (dateString.includes(" ")) {
      return dateString.split(" ")[1];
    }
    const d = new Date(dateString);
    return d.toLocaleTimeString("es-ES", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  const totalCitas = citasHoy.length;
  const completadas = citasHoy.filter((c) => Number(c.id_estado_cita) === 4).length;
  const pendientes = citasHoy.filter(
    (c) => Number(c.id_estado_cita) === 1 || Number(c.id_estado_cita) === 3
  ).length;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[350px] gap-3 opacity-60">
        <div className="w-10 h-10 border-4 border-[#148F77] border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-black uppercase tracking-widest text-[#148F77]">
          Cargando Agenda Diaria...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* BANNER GREETING */}
      <div className="bg-gradient-to-r from-[#2A5C4D] to-[#148F77] text-white p-8 md:p-10 rounded-[2.5rem] shadow-xl relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="relative z-10 space-y-2">
          <span className="bg-white/20 text-white text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full shadow-sm">
            Recepción y Atención
          </span>
          <h1 className="text-3xl md:text-4xl font-black italic tracking-tight">
            Hola, {user?.nombre || "Recepcionista"}
          </h1>
          <p className="opacity-80 text-xs md:text-sm max-w-lg leading-relaxed">
            Monitorea las llegadas de pacientes, gestiona la disponibilidad de las salas clínicas y agenda nuevas atenciones para el día.
          </p>
        </div>
        <button
          onClick={openModal}
          className="relative z-10 px-6 py-3.5 bg-white text-[#2A5C4D] hover:bg-emerald-50 transition-all font-black text-xs uppercase tracking-wider rounded-2xl shadow-lg active:scale-95 cursor-pointer flex items-center gap-2"
        >
          <span className="text-base font-light">+</span> Nueva Cita Rápida
        </button>
        {/* Decoración de fondo */}
        <div className="absolute -right-20 -bottom-20 w-80 h-80 bg-white/5 rounded-full blur-3xl"></div>
      </div>

      {/* METRICS GRID */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* CITAS DE HOY */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Citas de Hoy</p>
              <h3 className="text-2xl font-black text-[#2A5C4D]">{totalCitas}</h3>
            </div>
            <div className="p-3 bg-emerald-50 text-[#148F77] rounded-2xl">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-gray-400 font-bold mt-4">
            Total citas agendadas para hoy
          </p>
        </div>

        {/* CITAS PENDIENTES */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Pendientes Hoy</p>
              <h3 className="text-2xl font-black text-blue-600">{pendientes}</h3>
            </div>
            <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-blue-600 font-bold mt-4">
            Citas programadas por atender
          </p>
        </div>

        {/* CITAS COMPLETADAS */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Completadas Hoy</p>
              <h3 className="text-2xl font-black text-emerald-600">{completadas}</h3>
            </div>
            <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-emerald-600 font-bold mt-4">
            Atenciones finalizadas con éxito
          </p>
        </div>

        {/* PACIENTES EN EL SISTEMA */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Fichas de Pacientes</p>
              <h3 className="text-2xl font-black text-gray-800">{dataMaster?.pacientes?.length || 0}</h3>
            </div>
            <div className="p-3 bg-gray-50 text-gray-500 rounded-2xl">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-gray-400 font-bold mt-4">
            {dataMaster?.salas?.length || 0} Salas clínicas registradas
          </p>
        </div>
      </div>

      {/* AGENDA DE HOY */}
      <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-black text-[#2A5C4D]">Agenda del Día</h2>
            <p className="text-gray-400 text-xs">Citas programadas para la jornada de hoy</p>
          </div>
          <button 
            onClick={() => setView("Citas")}
            className="text-[#148F77] text-xs font-black uppercase tracking-wider hover:underline"
          >
            Ver Calendario Completo
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold text-center">
            {error}
          </div>
        )}

        {!error && citasHoy.length === 0 ? (
          <div className="text-center py-12 opacity-50 space-y-2 border-2 border-dashed border-gray-100 rounded-2xl">
            <p className="text-sm font-black text-[#2A5C4D] uppercase tracking-widest">Sin Consultas Registradas</p>
            <p className="text-xs text-gray-400">No hay citas programadas para el día de hoy.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="pb-3 text-[10px] font-black text-gray-400 uppercase tracking-wider">Hora</th>
                  <th className="pb-3 text-[10px] font-black text-gray-400 uppercase tracking-wider">Paciente</th>
                  <th className="pb-3 text-[10px] font-black text-gray-400 uppercase tracking-wider">Odontólogo</th>
                  <th className="pb-3 text-[10px] font-black text-gray-400 uppercase tracking-wider">Sala</th>
                  <th className="pb-3 text-[10px] font-black text-gray-400 uppercase tracking-wider">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {citasHoy.map((cita) => {
                  const estadoColors =
                    ESTADO_CITA_COLORS[cita.id_estado_cita] ||
                    ESTADO_CITA_COLORS[ESTADO_CITA.PROGRAMADA];
                  const estadoLabel =
                    cita.nombre_estado ||
                    ESTADO_CITA_LABELS[cita.id_estado_cita] ||
                    `Estado ${cita.id_estado_cita}`;

                  return (
                    <tr key={cita.id_cita} className="group hover:bg-gray-50/50 transition-colors">
                      <td className="py-4 text-sm font-black text-[#2A5C4D]">{formatTime(cita.fecha_agendamiento)}</td>
                      <td className="py-4 text-xs font-bold text-gray-700">{getPacienteName(cita.id_paciente)}</td>
                      <td className="py-4 text-xs font-bold text-gray-500">{getOdontologoName(cita.id_personal)}</td>
                      <td className="py-4 text-xs text-gray-400 font-bold">{getSalaName(cita.id_sala)}</td>
                      <td className="py-4">
                        <span className={`text-[8px] font-black uppercase tracking-wider px-2.5 py-1.5 rounded-lg text-center ${estadoColors.badge}`}>
                          {estadoLabel}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ACCESOS OPERATIVOS */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <button
          onClick={() => setView("Pacientes")}
          className="flex items-center gap-4 p-5 bg-white border border-gray-100 rounded-3xl hover:shadow-md transition-all text-left cursor-pointer group"
        >
          <div className="p-3 bg-emerald-50 text-[#148F77] rounded-2xl group-hover:scale-110 transition-transform">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <div>
            <h4 className="text-xs font-black text-gray-800 uppercase tracking-wider">Ver Fichas Pacientes</h4>
            <p className="text-[10px] text-gray-400 mt-0.5">Crear o buscar historial de pacientes</p>
          </div>
        </button>

        <button
          onClick={() => setView("Citas")}
          className="flex items-center gap-4 p-5 bg-white border border-gray-100 rounded-3xl hover:shadow-md transition-all text-left cursor-pointer group"
        >
          <div className="p-3 bg-teal-50 text-[#148F77] rounded-2xl group-hover:scale-110 transition-transform">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h4 className="text-xs font-black text-gray-800 uppercase tracking-wider">Ver Calendario</h4>
            <p className="text-[10px] text-gray-400 mt-0.5">Controlar la agenda general e inasistencias</p>
          </div>
        </button>

        <button
          onClick={() => setView("Pagos y Saldos")}
          className="flex items-center gap-4 p-5 bg-white border border-gray-100 rounded-3xl hover:shadow-md transition-all text-left cursor-pointer group"
        >
          <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl group-hover:scale-110 transition-transform">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <div>
            <h4 className="text-xs font-black text-gray-800 uppercase tracking-wider">Cobrar en Caja</h4>
            <p className="text-[10px] text-gray-400 mt-0.5">Registrar pagos y saldos de pacientes</p>
          </div>
        </button>
      </div>
    </div>
  );
}