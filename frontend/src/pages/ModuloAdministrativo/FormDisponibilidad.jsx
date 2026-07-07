import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL;

export default function FormDisponibilidad({ onClose, onSuccess }) {

    const token = localStorage.getItem("token");

    const headers = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
    };

    const hoy = new Date().toISOString().split("T")[0];

    const [personal, setPersonal] = useState([]);

    const [form, setForm] = useState({

        id_personal: "",

        fecha_inicio: "",

        fecha_fin: "",

        motivo: "Vacaciones",

        observacion: ""

    });

    const [saving, setSaving] = useState(false);

    const [error, setError] = useState("");

    const [success, setSuccess] = useState("");


    // =====================================
    // CARGAR PERSONAL
    // =====================================

    const fetchPersonal = async () => {

        try {

            const res = await fetch(
                `${API_URL}/personal`,
                {
                    headers
                }
            );

            const data = await res.json();

            setPersonal(data.data || []);

        }
        catch {

            setError("No se pudo cargar el personal.");

        }

    };


    useEffect(() => {

        fetchPersonal();

    }, []);



    // =====================================
    // CAMBIOS
    // =====================================

    const handleChange = (e) => {

        setError("");

        setSuccess("");

        setForm({

            ...form,

            [e.target.name]: e.target.value

        });

    };



    // =====================================
    // CALCULAR DIAS
    // =====================================

    const calcularDias = () => {

        if(!form.fecha_inicio || !form.fecha_fin)
            return 0;


        const inicio = new Date(form.fecha_inicio);

        const fin = new Date(form.fecha_fin);


        return (

            Math.floor(
                (fin - inicio) /
                (1000 * 60 * 60 * 24)
            ) + 1

        );

    };



    // =====================================
    // GUARDAR
    // =====================================

    const guardar = async (e) => {

        e.preventDefault();


        setError("");

        setSuccess("");



        if(
            !form.id_personal ||
            !form.fecha_inicio ||
            !form.fecha_fin ||
            !form.motivo
        ){

            setError(
                "Complete todos los campos obligatorios."
            );

            return;

        }



        const inicio = new Date(form.fecha_inicio);

        const fin = new Date(form.fecha_fin);

        const fechaActual = new Date();

        fechaActual.setHours(0,0,0,0);



        if(inicio < fechaActual){

            setError(
                "La fecha de inicio no puede ser anterior a la fecha actual."
            );

            return;

        }



        if(fin < inicio){

            setError(
                "La fecha fin debe ser mayor o igual a la fecha inicio."
            );

            return;

        }



        const dias = calcularDias();


        if(dias > 5){

            setError(
                "La disponibilidad no puede superar los 5 días."
            );

            return;

        }



        if(form.observacion.length > 250){

            setError(
                "La observación no puede superar los 250 caracteres."
            );

            return;

        }



        setSaving(true);



        try {


            const res = await fetch(

                `${API_URL}/disponibilidad`,

                {

                    method:"POST",

                    headers,

                    body: JSON.stringify(form)

                }

            );



            const data = await res.json();



            if(!res.ok){

                setError(
                    data.message || "Error al registrar."
                );

                setSaving(false);

                return;

            }



            setSuccess(
                "Disponibilidad registrada correctamente."
            );



            setTimeout(() => {

                onSuccess();

            },700);



        }

        catch {

            setError(
                "Error de conexión con el servidor."
            );

        }



        setSaving(false);


    };



    return (

        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">


            <div className="bg-white rounded-3xl shadow-2xl w-full max-w-xl animate-fade-in">



                {/* HEADER */}

                <div className="border-b border-gray-100 px-8 py-6">


                    <h2 className="text-2xl font-black text-[#2A5C4D]">

                        Registrar Disponibilidad

                    </h2>


                    <p className="text-xs uppercase tracking-widest text-gray-400 mt-1">

                        Vacaciones, permisos y bajas médicas

                    </p>


                </div>



                <form
                    onSubmit={guardar}
                    className="p-8 space-y-6"
                >



                    {
                        error &&

                        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm font-bold">

                            {error}

                        </div>

                    }



                    {
                        success &&

                        <div className="bg-green-50 border border-green-200 text-green-700 rounded-xl px-4 py-3 text-sm font-bold">

                            {success}

                        </div>

                    }



                    {/* PERSONAL */}

                    <div>

                        <label className="block text-xs font-black uppercase text-gray-500 mb-2">

                            Personal

                        </label>


                        <select

                            name="id_personal"

                            value={form.id_personal}

                            onChange={handleChange}

                            className="w-full border border-gray-200 rounded-2xl px-4 py-3 outline-none focus:border-[#148F77]"

                        >

                            <option value="">

                                Seleccione...

                            </option>


                            {
                                personal.map((p)=>(

                                    <option

                                        key={p.id_personal}

                                        value={p.id_personal}

                                    >

                                        {p.nombre}

                                    </option>

                                ))
                            }


                        </select>

                    </div>



                    {/* FECHAS */}

                    <div className="grid grid-cols-2 gap-4">


                        <div>

                            <label className="block text-xs font-black uppercase text-gray-500 mb-2">

                                Fecha Inicio

                            </label>


                            <input

                                type="date"

                                name="fecha_inicio"

                                min={hoy}

                                value={form.fecha_inicio}

                                onChange={handleChange}

                                className="w-full border border-gray-200 rounded-2xl px-4 py-3"

                            />

                        </div>



                        <div>

                            <label className="block text-xs font-black uppercase text-gray-500 mb-2">

                                Fecha Fin

                            </label>


                            <input

                                type="date"

                                name="fecha_fin"

                                min={form.fecha_inicio || hoy}

                                value={form.fecha_fin}

                                onChange={handleChange}

                                className="w-full border border-gray-200 rounded-2xl px-4 py-3"

                            />


                        </div>


                    </div>



                    {
                        calcularDias() > 0 &&

                        <p
                            className={`text-xs font-black ${
                                calcularDias() > 5
                                ? "text-red-600"
                                : "text-[#148F77]"
                            }`}
                        >

                            Días solicitados: {calcularDias()} / 5

                        </p>

                    }



                    {/* MOTIVO */}

                    <div>

                        <label className="block text-xs font-black uppercase text-gray-500 mb-2">

                            Motivo

                        </label>


                        <select

                            name="motivo"

                            value={form.motivo}

                            onChange={handleChange}

                            className="w-full border border-gray-200 rounded-2xl px-4 py-3"

                        >

                            <option>Vacaciones</option>

                            <option>Baja Médica</option>

                            <option>Permiso</option>

                            <option>Capacitación</option>

                            <option>Congreso</option>

                            <option>Otro</option>


                        </select>

                    </div>



                    {/* OBSERVACION */}

                    <div>

                        <label className="block text-xs font-black uppercase text-gray-500 mb-2">

                            Observación

                        </label>


                        <textarea

                            rows={4}

                            maxLength={250}

                            name="observacion"

                            value={form.observacion}

                            onChange={handleChange}

                            className="w-full border border-gray-200 rounded-2xl px-4 py-3 resize-none"

                        />

                        <p className="text-xs text-gray-400 mt-1">

                            {form.observacion.length}/250 caracteres

                        </p>


                    </div>



                    {/* BOTONES */}

                    <div className="flex justify-end gap-4 pt-4">


                        <button

                            type="button"

                            onClick={onClose}

                            className="px-6 py-3 rounded-2xl bg-gray-100 hover:bg-gray-200 text-gray-700 font-black"

                        >

                            Cancelar

                        </button>



                        <button

                            disabled={saving}

                            type="submit"

                            className="px-8 py-3 rounded-2xl bg-[#148F77] hover:bg-[#0f6b59] text-white font-black"

                        >

                            {
                                saving
                                ? "Guardando..."
                                : "Guardar"
                            }


                        </button>


                    </div>



                </form>


            </div>


        </div>

    );

}