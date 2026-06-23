import { useState, useEffect } from "react";
import {
  ESTADO_CITA,
  ESTADO_CITA_LABELS,
  ESTADO_CITA_COLORS,
} from "../../constants/enums";

const API_URL = import.meta.env.VITE_API_URL;

export default function DashboardOdontologo({ user, dataMaster, setView, openModal }) {
  const [loading, setLoading] = useState(true);
  const [citasList, setCitasList] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCitasDoc = async () => {
      setLoading(true);
      setError(null);
      try {
        const idPersona = user?.id_persona || "";
        if (!idPersona) {
          setError("No se pudo asociar la sesión al odontólogo actual.");
          setLoading(false);
          return;
        }

        const headers = {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        };

        const res = await fetch(
          `${API_URL}/citas?page=1&limit=1000&id_personal=${idPersona}`,
          { headers }
        );
        const data = await res.json();

        if (data.success !== false) {
          setCitasList(data.data || []);
        } else {
          setError(data.message || "Error al cargar su agenda médica.");
        }
      } catch (err) {
        console.error("Error fetching doctor stats:", err);
        setError("Error de conexión al cargar la agenda de citas.");
      } finally {
        setLoading(false);
      }
    };

    fetchCitasDoc();
  }, [user]);

  const getPacienteName = (id) => {
    if (!dataMaster?.pacientes) return id;
    const paciente = dataMaster.pacientes.find(
      (p) => (p.id_persona || p.id_usuario || p.id) == id
    );
    return paciente ? paciente.nombre : `Paciente #${id}`;
  };

  const getSalaName = (id) => {
    if (!dataMaster?.salas) return `Sala #${id}`;
    const sala = dataMaster.salas.find((s) => s.id_sala == id);
    return sala ? sala.nombre : `Sala #${id}`;
  };

  // Helper formatting dates & times
  const getTodayDateStr = () => {
    const now = new Date();
    const d = String(now.getDate()).padStart(2, "0");
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const y = String(now.getFullYear()).slice(-2);
    return `${d}/${m}/${y}`;
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

  // Stats computation
  const todayStr = getTodayDateStr();
  const todayCitas = citasList.filter(
    (c) => c.fecha_agendamiento && c.fecha_agendamiento.startsWith(todayStr)
  );

  const totalCitas = citasList.length;
  const completadas = citasList.filter((c) => Number(c.id_estado_cita) === 4).length;
  const canceladas = citasList.filter((c) => Number(c.id_estado_cita) === 2).length;
  const noAsistio = citasList.filter((c) => Number(c.id_estado_cita) === 5).length;
  const programadas = citasList.filter(
    (c) => Number(c.id_estado_cita) === 1 || Number(c.id_estado_cita) === 3
  ).length;

  // Percentage of successful/completed appointments
  const totalCerradas = completadas + canceladas + noAsistio;
  const exitosasPorcentaje = totalCerradas
    ? Math.round((completadas / totalCerradas) * 100)
    : 100;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[350px] gap-3 opacity-60">
        <div className="w-10 h-10 border-4 border-[#148F77] border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-black uppercase tracking-widest text-[#148F77]">
          Cargando Agenda de Especialidad...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* BANNER BIENVENIDA */}
      <div className="bg-gradient-to-r from-[#2A5C4D] to-[#148F77] text-white p-8 md:p-10 rounded-[2.5rem] shadow-xl relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="relative z-10 space-y-2">
          <span className="bg-white/20 text-white text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full shadow-sm">
            Portal Odontológico
          </span>
          <h1 className="text-3xl md:text-4xl font-black italic tracking-tight">
            Dr(a). {user?.nombre || "Especialista"}
          </h1>
          <p className="opacity-80 text-xs md:text-sm max-w-lg leading-relaxed">
            Consulte su agenda de citas asignadas para hoy, analice sus métricas de rendimiento y registre la atención presencial de sus pacientes.
          </p>
        </div>
        <button
          onClick={openModal}
          className="relative z-10 px-6 py-3.5 bg-white text-[#2A5C4D] hover:bg-emerald-50 transition-all font-black text-xs uppercase tracking-wider rounded-2xl shadow-lg active:scale-95 cursor-pointer flex items-center gap-2"
        >
          <span className="text-base font-light">+</span> Registrar Atención
        </button>
        {/* Decoración de fondo */}
        <div className="absolute -right-20 -bottom-20 w-80 h-80 bg-white/5 rounded-full blur-3xl"></div>
      </div>

      {/* METRIC CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* TOTAL CITAS ASIGNADAS */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Citas Históricas</p>
              <h3 className="text-2xl font-black text-gray-800">{totalCitas}</h3>
            </div>
            <div className="p-3 bg-gray-50 text-gray-500 rounded-2xl">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-gray-400 font-bold mt-4">
            Total citas acumuladas en su historial
          </p>
        </div>

        {/* CITAS COMPLETADAS */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Citas Completadas</p>
              <h3 className="text-2xl font-black text-emerald-600">{completadas}</h3>
            </div>
            <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-emerald-600 font-bold mt-4">
            Atenciones clínicas finalizadas
          </p>
        </div>

        {/* CITAS AGENDADAS PARA HOY */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Citas para Hoy</p>
              <h3 className="text-2xl font-black text-blue-600">{todayCitas.length}</h3>
            </div>
            <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-blue-600 font-bold mt-4">
            Consultas agendadas el día de hoy
          </p>
        </div>

        {/* PORCENTAJE CITAS BUENAS */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">% de Citas Buenas</p>
              <h3 className={`text-2xl font-black ${exitosasPorcentaje >= 80 ? "text-emerald-600" : "text-amber-600"}`}>
                {exitosasPorcentaje}%
              </h3>
            </div>
            <div className={`p-3 rounded-2xl ${exitosasPorcentaje >= 80 ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"}`}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-gray-400 font-bold mt-4">
            Porcentaje de citas completadas del total cerrado
          </p>
        </div>
      </div>

      {/* AGENDA DEL ODONTÓLOGO DE HOY */}
      <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-black text-[#2A5C4D]">Su Agenda de Hoy</h2>
            <p className="text-gray-400 text-xs">Citas asignadas en su horario para la fecha {todayStr}</p>
          </div>
          <button 
            onClick={() => setView("Citas")}
            className="text-[#148F77] text-xs font-black uppercase tracking-wider hover:underline"
          >
            Ver Mi Calendario Completo
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold text-center">
            {error}
          </div>
        )}

        {!error && todayCitas.length === 0 ? (
          <div className="text-center py-12 opacity-50 space-y-2 border-2 border-dashed border-gray-100 rounded-2xl">
            <p className="text-sm font-black text-[#2A5C4D] uppercase tracking-widest">Día Libre o Sin Consultas</p>
            <p className="text-xs text-gray-400">No tiene citas asignadas para hoy.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {todayCitas.map((cita) => {
              const estadoColors =
                ESTADO_CITA_COLORS[cita.id_estado_cita] ||
                ESTADO_CITA_COLORS[ESTADO_CITA.PROGRAMADA];
              const estadoLabel =
                cita.nombre_estado ||
                ESTADO_CITA_LABELS[cita.id_estado_cita] ||
                `Estado ${cita.id_estado_cita}`;

              return (
                <div key={cita.id_cita} className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 bg-gray-50 border border-gray-100 rounded-2xl hover:shadow-sm transition-shadow gap-4">
                  <div className="flex items-center gap-4">
                    <div className="text-center bg-white px-4 py-2.5 rounded-xl border border-gray-100 min-w-[70px]">
                      <p className="text-[10px] text-gray-400 font-bold uppercase">Hora</p>
                      <p className="text-xs font-black text-[#2A5C4D]">{formatTime(cita.fecha_agendamiento)}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Paciente</p>
                      <h4 className="text-sm font-bold text-gray-700">{getPacienteName(cita.id_paciente)}</h4>
                      <p className="text-[10px] text-gray-400 font-bold mt-0.5">
                        {getSalaName(cita.id_sala)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                    <span className={`text-[8px] font-black uppercase tracking-wider px-2.5 py-1.5 rounded-lg text-center ${estadoColors.badge}`}>
                      {estadoLabel}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}