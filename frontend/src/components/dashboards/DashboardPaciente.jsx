import { useState, useEffect } from "react";
import {
  ESTADO_CITA,
  ESTADO_CITA_LABELS,
  ESTADO_CITA_COLORS,
} from "../../constants/enums";

const API_URL = import.meta.env.VITE_API_URL;

export default function DashboardPaciente({ user, dataMaster, setView, openModal }) {
  const [loading, setLoading] = useState(true);
  const [citas, setCitas] = useState([]);
  const [saldos, setSaldos] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPacienteData = async () => {
      setLoading(true);
      setError(null);
      try {
        const idPersona = user?.id_persona || "";
        if (!idPersona) {
          setError("No se pudo asociar la sesión al paciente actual.");
          setLoading(false);
          return;
        }

        const headers = {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        };

        const [resCitas, resSaldos] = await Promise.all([
          fetch(`${API_URL}/citas?page=1&limit=100&id_paciente=${idPersona}`, { headers }).then((r) => r.json()),
          fetch(`${API_URL}/finanzas/saldos/paciente/${idPersona}`, { headers }).then((r) => r.json()),
        ]);

        if (resCitas.success !== false) {
          setCitas(resCitas.data || []);
        }
        if (resSaldos.success !== false) {
          setSaldos(resSaldos.data || []);
        }
      } catch (err) {
        console.error("Error fetching patient stats:", err);
        setError("Error de conexión al cargar sus datos clínicos y de facturación.");
      } finally {
        setLoading(false);
      }
    };

    fetchPacienteData();
  }, [user]);

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

  const formatCurrency = (val) => {
    return new Intl.NumberFormat("es-BO", {
      style: "currency",
      currency: "BOB",
      minimumFractionDigits: 2,
    }).format(val);
  };

  // Computations
  const upcomingCitas = citas.filter(
    (c) => Number(c.id_estado_cita) === 1 || Number(c.id_estado_cita) === 3
  );

  let saldoPendiente = 0;
  let totalInvertido = 0;

  saldos.forEach((s) => {
    const inicial = parseFloat(s.saldo_inicial_bob) || 0;
    const actual = parseFloat(s.saldo_actual_bob) || 0;
    saldoPendiente += actual;
    totalInvertido += (inicial - actual);
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[350px] gap-3 opacity-60">
        <div className="w-10 h-10 border-4 border-[#148F77] border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-black uppercase tracking-widest text-[#148F77]">
          Cargando Información de Paciente...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* HEADER BANNER */}
      <div className="bg-gradient-to-br from-[#148F77] to-[#2A5C4D] text-white p-8 md:p-12 rounded-[2.5rem] shadow-2xl relative overflow-hidden flex flex-col justify-between items-start gap-6">
        <div className="relative z-10 space-y-3">
          <span className="bg-white/20 text-white text-[9px] font-black uppercase tracking-widest px-3 py-1.5 rounded-full shadow-sm">
            Portal del Paciente
          </span>
          <h2 className="text-3xl md:text-4xl font-black mb-3 tracking-tighter italic max-w-xl">
            Cuidamos tu Sonrisa, queremos que seas la mejor versión de ti
          </h2>
          <p className="opacity-80 text-xs md:text-sm leading-relaxed max-w-md">
            Agenda tu cita hoy mismo con nuestros especialistas de forma rápida. 
            Horarios de atención: Lun-Vie (08:00-19:00) y Sáb (09:00-13:00).
          </p>
        </div>
        <button
          onClick={openModal}
          className="relative z-10 bg-white hover:bg-emerald-50 text-[#2A5C4D] font-black text-xs uppercase tracking-widest px-8 py-4 rounded-full shadow-md transition-all hover:scale-[1.02] active:scale-95 cursor-pointer"
        >
          AGENDAR CITA AHORA ➔
        </button>
        {/* Decorative elements */}
        <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-white/5 rounded-full blur-3xl"></div>
      </div>

      {/* METRICS GRID */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {/* MIS CITAS PROGRAMADAS */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Próximas Citas</p>
              <h3 className="text-2xl font-black text-[#2A5C4D]">{upcomingCitas.length}</h3>
            </div>
            <div className="p-3 bg-emerald-50 text-[#148F77] rounded-2xl">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-gray-400 font-bold mt-4">
            Citas futuras programadas
          </p>
        </div>

        {/* SALDO PENDIENTE */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Saldo Pendiente</p>
              <h3 className={`text-2xl font-black ${saldoPendiente > 0 ? "text-blue-600" : "text-emerald-600"}`}>
                {formatCurrency(saldoPendiente)}
              </h3>
            </div>
            <div className={`p-3 rounded-2xl ${saldoPendiente > 0 ? "bg-blue-50 text-blue-600" : "bg-emerald-50 text-emerald-600"}`}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-gray-400 font-bold mt-4">
            Cuentas pendientes por pagar
          </p>
        </div>

        {/* TOTAL PAGADO (INVERTIDO) */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Total Abonado</p>
              <h3 className="text-2xl font-black text-gray-800">{formatCurrency(totalInvertido)}</h3>
            </div>
            <div className="p-3 bg-gray-50 text-gray-500 rounded-2xl">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-gray-400 font-bold mt-4">
            Importe total pagado en tratamientos
          </p>
        </div>
      </div>

      {/* DETALLES DE AGENDA FUTURA */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* PRÓXIMAS VISITAS */}
        <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-black text-[#2A5C4D]">Próximas Visitas</h2>
              <p className="text-gray-400 text-xs">Sus citas programadas con nuestros especialistas</p>
            </div>
            <button 
              onClick={() => setView("Citas")}
              className="text-[#148F77] text-xs font-black uppercase tracking-wider hover:underline"
            >
              Mis Citas
            </button>
          </div>

          {error && (
            <div className="p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold text-center">
              {error}
            </div>
          )}

          {!error && upcomingCitas.length === 0 ? (
            <div className="text-center py-10 opacity-50 space-y-2 border border-dashed border-gray-100 rounded-2xl">
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Sin Citas Pendientes</p>
              <p className="text-[10px] text-gray-400">¿Necesitas una consulta? Agenda una cita arriba.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {upcomingCitas.map((cita) => {
                const estadoColors =
                  ESTADO_CITA_COLORS[cita.id_estado_cita] ||
                  ESTADO_CITA_COLORS[ESTADO_CITA.PROGRAMADA];
                const estadoLabel =
                  cita.nombre_estado ||
                  ESTADO_CITA_LABELS[cita.id_estado_cita] ||
                  `Estado ${cita.id_estado_cita}`;

                return (
                  <div key={cita.id_cita} className="flex justify-between items-center p-4 bg-gray-50 border border-gray-100 rounded-2xl">
                    <div>
                      <span className="text-[9px] font-black text-[#148F77] uppercase tracking-widest">
                        {cita.fecha_agendamiento ? cita.fecha_agendamiento.split(" ")[0] : ""}
                      </span>
                      <h4 className="text-sm font-bold text-gray-700 mt-0.5">
                        Hora: {cita.fecha_agendamiento ? cita.fecha_agendamiento.split(" ")[1] : ""}
                      </h4>
                      <p className="text-[10px] text-gray-400 font-bold mt-1">
                        Especialista: {getOdontologoName(cita.id_personal)} | {getSalaName(cita.id_sala)}
                      </p>
                    </div>
                    <span className={`text-[8px] font-black uppercase tracking-wider px-2.5 py-1.5 rounded-lg ${estadoColors.badge}`}>
                      {estadoLabel}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* HISTORIAL FINANCIERO */}
        <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-black text-[#2A5C4D]">Historial de Cuentas</h2>
              <p className="text-gray-400 text-xs">Cargos y pagos de sus consultas registradas</p>
            </div>
            <button 
              onClick={() => setView("Pagos y Saldos")}
              className="text-[#148F77] text-xs font-black uppercase tracking-wider hover:underline"
            >
              Realizar Pago
            </button>
          </div>

          {!error && saldos.length === 0 ? (
            <div className="text-center py-10 opacity-50 space-y-2 border border-dashed border-gray-100 rounded-2xl">
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Sin Cuentas Registradas</p>
              <p className="text-[10px] text-gray-400">No cuenta con registros de facturación vigentes.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {saldos.slice(0, 3).map((s) => {
                const total = parseFloat(s.saldo_inicial_bob) || 0;
                const pendiente = parseFloat(s.saldo_actual_bob) || 0;
                const abonado = total - pendiente;

                return (
                  <div key={s.id_saldo} className="p-4 bg-gray-50 border border-gray-100 rounded-2xl flex flex-col gap-2">
                    <div className="flex justify-between items-center text-xs font-bold text-gray-700">
                      <span>Consulta del {s.fecha_agendamiento ? s.fecha_agendamiento.split(" ")[0] : ""}</span>
                      <span className={`${pendiente > 0 ? "text-blue-600" : "text-emerald-600"}`}>
                        {pendiente > 0 ? `Debe ${formatCurrency(pendiente)}` : "Pagado"}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-[#148F77] h-full rounded-full" style={{ width: `${(abonado / (total || 1)) * 100}%` }}></div>
                    </div>
                    <div className="flex justify-between text-[9px] text-gray-400 font-bold uppercase tracking-wider">
                      <span>Abonado: {formatCurrency(abonado)}</span>
                      <span>Total: {formatCurrency(total)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}