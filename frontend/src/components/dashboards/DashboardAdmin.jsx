import { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL;

export default function DashboardAdmin({ user, dataMaster, setView }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    ingresos: 0,
    deuda: 0,
    programadas: 0,
    completadas: 0,
    canceladas: 0,
    noAsistio: 0,
    totalCitas: 0,
    alertasCount: 0,
  });
  const [alertasStock, setAlertasStock] = useState([]);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      setError(null);
      try {
        const headers = {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        };

        // Fetch saldos, citas, and alertas in parallel
        const [resSaldos, resCitas, resAlertas] = await Promise.all([
          fetch(`${API_URL}/finanzas/saldos`, { headers }).then((r) => r.json()),
          fetch(`${API_URL}/citas?page=1&limit=1000`, { headers }).then((r) => r.json()),
          fetch(`${API_URL}/inventario/alertas`, { headers }).then((r) => r.json()),
        ]);

        let ingresos = 0;
        let deuda = 0;
        if (resSaldos.success && Array.isArray(resSaldos.data)) {
          resSaldos.data.forEach((s) => {
            const inicial = parseFloat(s.saldo_inicial_bob) || 0;
            const actual = parseFloat(s.saldo_actual_bob) || 0;
            ingresos += (inicial - actual);
            deuda += actual;
          });
        }

        let prog = 0;
        let comp = 0;
        let canc = 0;
        let noAs = 0;
        let totalC = 0;

        const citasList = resCitas?.data || [];
        if (Array.isArray(citasList)) {
          totalC = citasList.length;
          citasList.forEach((c) => {
            const state = Number(c.id_estado_cita);
            if (state === 1 || state === 3) prog++;      // Programada o Reprogramada
            else if (state === 4) comp++;                // Completada
            else if (state === 2) canc++;                // Cancelada
            else if (state === 5) noAs++;                // No Asistió
          });
        }

        let rawStockAlerts = [];
        let rawVencAlerts = [];
        let stockCount = 0;
        let vencCount = 0;

        if (resAlertas.success) {
          rawStockAlerts = resAlertas.stock_bajo || [];
          rawVencAlerts = resAlertas.por_vencer || [];
          stockCount = rawStockAlerts.length;
          vencCount = rawVencAlerts.length;
        }

        setStats({
          ingresos,
          deuda,
          programadas: prog,
          completadas: comp,
          canceladas: canc,
          noAsistio: noAs,
          totalCitas: totalC,
          alertasCount: stockCount + vencCount,
        });

        setAlertasStock(rawStockAlerts.slice(0, 4)); // Show top 4 alerts
      } catch (err) {
        console.error("Error fetching admin stats:", err);
        setError("Error al cargar la información estadística en tiempo real.");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const formatCurrency = (val) => {
    return new Intl.NumberFormat("es-BO", {
      style: "currency",
      currency: "BOB",
      minimumFractionDigits: 2,
    }).format(val);
  };

  const getPercent = (count) => {
    if (!stats.totalCitas) return "0%";
    return `${Math.round((count / stats.totalCitas) * 100)}%`;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[350px] gap-3 opacity-60">
        <div className="w-10 h-10 border-4 border-[#148F77] border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-black uppercase tracking-widest text-[#148F77]">
          Cargando Panel de Control...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* BANNER DE BIENVENIDA */}
      <div className="bg-gradient-to-r from-[#2A5C4D] to-[#148F77] text-white p-8 md:p-10 rounded-[2.5rem] shadow-xl relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="relative z-10 space-y-2">
          <span className="bg-white/20 text-white text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full shadow-sm">
            Control de Administración
          </span>
          <h1 className="text-3xl md:text-4xl font-black italic tracking-tight">
            Hola, {user?.nombre || "Administrador"}
          </h1>
          <p className="opacity-80 text-xs md:text-sm max-w-lg leading-relaxed">
            Bienvenido al centro de control clínico. Monitorea ingresos, deudas pendientes, inventario crítico y el estado general de la agenda.
          </p>
        </div>
        <div className="bg-white/10 px-6 py-4 rounded-3xl backdrop-blur-sm border border-white/10 flex flex-col justify-center text-center">
          <p className="text-[9px] uppercase font-bold opacity-60 tracking-wider">Estado de Servicios</p>
          <p className="text-xl font-black text-emerald-300 animate-pulse">100% ONLINE</p>
        </div>
        {/* Decoración de fondo */}
        <div className="absolute -right-20 -bottom-20 w-80 h-80 bg-white/5 rounded-full blur-3xl"></div>
      </div>

      {/* METRIC CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* INGRESOS CARD */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between relative overflow-hidden group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Ingresos Registrados</p>
              <h3 className="text-2xl font-black text-[#2A5C4D]">{formatCurrency(stats.ingresos)}</h3>
            </div>
            <div className="p-3 bg-emerald-50 text-[#148F77] rounded-2xl group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-[#148F77] font-bold mt-4 flex items-center gap-1">
            <span>●</span> Suma de abonos completados
          </p>
        </div>

        {/* CUENTAS POR COBRAR */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between relative overflow-hidden group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Cuentas por Cobrar</p>
              <h3 className="text-2xl font-black text-blue-600">{formatCurrency(stats.deuda)}</h3>
            </div>
            <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-blue-600 font-bold mt-4 flex items-center gap-1">
            <span>●</span> Saldo pendiente acumulado
          </p>
        </div>

        {/* PACIENTES CARD */}
        <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between relative overflow-hidden group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Pacientes Activos</p>
              <h3 className="text-2xl font-black text-gray-800">{dataMaster?.pacientes?.length || 0}</h3>
            </div>
            <div className="p-3 bg-gray-50 text-gray-500 rounded-2xl group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
          </div>
          <p className="text-[10px] text-gray-400 font-bold mt-4 flex items-center gap-1">
            <span>●</span> {dataMaster?.odontologos?.length || 0} Odontólogos en equipo
          </p>
        </div>

        {/* ALERTA INVENTARIO */}
        <div 
          onClick={() => setView("Gestionar Inventario")}
          className="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between relative overflow-hidden group cursor-pointer"
        >
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">Alertas Almacén</p>
              <h3 className={`text-2xl font-black ${stats.alertasCount > 0 ? "text-orange-500" : "text-emerald-600"}`}>
                {stats.alertasCount}
              </h3>
            </div>
            <div className={`p-3 rounded-2xl group-hover:scale-110 transition-transform ${stats.alertasCount > 0 ? "bg-orange-50 text-orange-500" : "bg-emerald-50 text-emerald-600"}`}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
          </div>
          <p className={`text-[10px] font-bold mt-4 flex items-center gap-1 ${stats.alertasCount > 0 ? "text-orange-500 animate-pulse" : "text-emerald-600"}`}>
            <span>●</span> {stats.alertasCount > 0 ? "Requiere reposición inmediata" : "Stock optimizado"}
          </p>
        </div>
      </div>

      {/* DETALLES DE CITAS E INVENTARIO BAJO */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* DISTRIBUCIÓN DE CITAS */}
        <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-black text-[#2A5C4D] tracking-tight">Distribución de Citas</h2>
              <p className="text-gray-400 text-xs">Análisis sobre un total de {stats.totalCitas} citas</p>
            </div>
            <button 
              onClick={() => setView("Citas")}
              className="text-[#148F77] text-xs font-black uppercase tracking-wider hover:underline"
            >
              Agenda Completa
            </button>
          </div>

          <div className="space-y-4">
            {/* COMPLETADAS */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-bold text-gray-600">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full"></span>
                  Completadas
                </span>
                <span>{stats.completadas} ({getPercent(stats.completadas)})</span>
              </div>
              <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full rounded-full transition-all duration-500" style={{ width: getPercent(stats.completadas) }}></div>
              </div>
            </div>

            {/* PROGRAMADAS */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-bold text-gray-600">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 bg-blue-500 rounded-full"></span>
                  Programadas / Reprog.
                </span>
                <span>{stats.programadas} ({getPercent(stats.programadas)})</span>
              </div>
              <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                <div className="bg-blue-500 h-full rounded-full transition-all duration-500" style={{ width: getPercent(stats.programadas) }}></div>
              </div>
            </div>

            {/* CANCELADAS */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-bold text-gray-600">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 bg-red-400 rounded-full"></span>
                  Canceladas
                </span>
                <span>{stats.canceladas} ({getPercent(stats.canceladas)})</span>
              </div>
              <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                <div className="bg-red-400 h-full rounded-full transition-all duration-500" style={{ width: getPercent(stats.canceladas) }}></div>
              </div>
            </div>

            {/* NO ASISTIÓ */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-bold text-gray-600">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 bg-orange-400 rounded-full"></span>
                  No Asistió
                </span>
                <span>{stats.noAsistio} ({getPercent(stats.noAsistio)})</span>
              </div>
              <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                <div className="bg-orange-400 h-full rounded-full transition-all duration-500" style={{ width: getPercent(stats.noAsistio) }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* ALERTA DE INSUMOS CRÍTICOS */}
        <div className="bg-white border border-gray-100 rounded-[2rem] p-8 shadow-sm flex flex-col justify-between space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-black text-[#2A5C4D] tracking-tight">Stock Crítico (Bajo)</h2>
              <p className="text-gray-400 text-xs">Reposición requerida de insumos clínicos</p>
            </div>
            <button 
              onClick={() => setView("Gestionar Inventario")}
              className="text-orange-500 text-xs font-black uppercase tracking-wider hover:underline"
            >
              Ver Almacén
            </button>
          </div>

          <div className="flex-1 flex flex-col justify-center">
            {alertasStock.length === 0 ? (
              <div className="text-center py-8 opacity-50 space-y-2">
                <div className="text-3xl text-emerald-500">✓</div>
                <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Inventario Óptimo</p>
                <p className="text-[10px] text-gray-400">Todos los insumos tienen stock por encima del mínimo.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alertasStock.map((alerta) => (
                  <div key={alerta.id_material} className="flex items-center justify-between p-3 bg-gray-50 rounded-2xl border border-gray-100">
                    <div>
                      <p className="text-xs font-bold text-gray-700">{alerta.nombre_material}</p>
                      <p className="text-[9px] text-gray-400 uppercase tracking-widest font-bold">
                        Disponible: {alerta.cantidad_disponible} uds (Mínimo: {alerta.cantidad_inicial})
                      </p>
                    </div>
                    <span className="text-[9px] font-black uppercase bg-red-100 text-red-600 px-2.5 py-1.5 rounded-lg">
                      {alerta.porcentaje}% restante
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ACCESOS RÁPIDOS */}
      <div className="bg-white border border-gray-100 rounded-[2.5rem] p-8 md:p-10 shadow-sm space-y-6">
        <div>
          <h2 className="text-xl font-black text-[#2A5C4D]">Accesos Rápidos</h2>
          <p className="text-gray-400 text-xs">Ejecución directa de funciones operativas clave</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* AUDITORÍA */}
          <button
            onClick={() => setView("Bitácora")}
            className="flex flex-col text-left p-6 rounded-3xl bg-amber-50 hover:bg-amber-100 transition-all duration-300 group border border-amber-100/50"
          >
            <div className="p-3 bg-amber-200/50 text-amber-800 rounded-2xl inline-block mb-4 w-fit">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h4 className="text-sm font-black text-amber-900 mb-1">Bitácora / Auditoría</h4>
            <p className="text-[10px] text-amber-800/80 leading-relaxed">Ver auditoría de seguridad y logs del sistema</p>
          </button>

          {/* CITAS */}
          <button
            onClick={() => setView("Citas")}
            className="flex flex-col text-left p-6 rounded-3xl bg-teal-50 hover:bg-teal-100 transition-all duration-300 group border border-teal-100/50"
          >
            <div className="p-3 bg-teal-200/50 text-teal-800 rounded-2xl inline-block mb-4 w-fit">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h4 className="text-sm font-black text-teal-900 mb-1">Calendario Clínico</h4>
            <p className="text-[10px] text-teal-800/80 leading-relaxed">Gestionar la agenda diaria de la clínica</p>
          </button>

          {/* FINANZAS */}
          <button
            onClick={() => setView("Pagos y Saldos")}
            className="flex flex-col text-left p-6 rounded-3xl bg-blue-50 hover:bg-blue-100 transition-all duration-300 group border border-blue-100/50"
          >
            <div className="p-3 bg-blue-200/50 text-blue-800 rounded-2xl inline-block mb-4 w-fit">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <h4 className="text-sm font-black text-blue-900 mb-1">Caja y Facturación</h4>
            <p className="text-[10px] text-blue-800/80 leading-relaxed">Registrar pagos, deudas y emitir recibos</p>
          </button>

          {/* INVENTARIO */}
          <button
            onClick={() => setView("Gestionar Inventario")}
            className="flex flex-col text-left p-6 rounded-3xl bg-emerald-50 hover:bg-emerald-100 transition-all duration-300 group border border-emerald-100/50"
          >
            <div className="p-3 bg-emerald-200/50 text-[#2A5C4D] rounded-2xl inline-block mb-4 w-fit">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <h4 className="text-sm font-black text-[#2A5C4D] mb-1">Logística de Inventario</h4>
            <p className="text-[10px] text-[#148F77] leading-relaxed">Controlar entradas, salidas y mermas</p>
          </button>
        </div>
      </div>
    </div>
  );
}