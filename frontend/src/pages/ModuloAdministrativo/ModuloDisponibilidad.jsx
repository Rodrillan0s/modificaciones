import { useEffect, useState } from "react";
import FormDisponibilidad from "./FormDisponibilidad";

const API_URL = import.meta.env.VITE_API_URL;

export default function ModuloDisponibilidad() {

    const token = localStorage.getItem("token");

    const headers = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
    };


    const [disponibilidad, setDisponibilidad] = useState([]);

    const [loading, setLoading] = useState(true);

    const [search, setSearch] = useState("");

    const [showCreate, setShowCreate] = useState(false);



    // ==========================================
    // FORMATO FECHA
    // ==========================================

   const formatearFecha = (fecha) => {

    if (!fecha)
        return "";

    const date = new Date(fecha);

    if (isNaN(date))
        return fecha;

    const dia = String(date.getDate()).padStart(2, "0");

    const mes = String(date.getMonth() + 1).padStart(2, "0");

    const anio = date.getFullYear();

    return `${dia}/${mes}/${anio}`;

};



    // ==========================================
    // CARGAR DISPONIBILIDAD
    // ==========================================

    const fetchDisponibilidad = async () => {

        try {

            const res = await fetch(
                `${API_URL}/disponibilidad`,
                {
                    headers
                }
            );


            const data = await res.json();


            setDisponibilidad(data.data || []);


        }
        catch(err){

            console.error(err);

        }
        finally{

            setLoading(false);

        }

    };



    useEffect(()=>{

        fetchDisponibilidad();

    },[]);



    // ==========================================
    // ELIMINAR
    // ==========================================

    const eliminar = async(id)=>{


        if(!window.confirm("¿Eliminar esta disponibilidad?"))
            return;


        try{


            await fetch(

                `${API_URL}/disponibilidad/${id}`,

                {

                    method:"DELETE",

                    headers

                }

            );


            fetchDisponibilidad();


        }
        catch(err){

            console.error(err);

        }


    };




    // ==========================================
    // FILTRO
    // ==========================================

    const filtered = disponibilidad.filter((d)=>{


        return (

            (d.nombre || "")
            .toLowerCase()
            .includes(search.toLowerCase())


            ||

            (d.motivo || "")
            .toLowerCase()
            .includes(search.toLowerCase())

        );


    });



    return (

        <div className="w-full p-4 md:p-8 space-y-8 animate-fade-in">



            {/* HEADER */}


            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-100 pb-5">


                <div>


                    <h2 className="text-3xl font-black text-[#2A5C4D] italic">

                        Administrar Disponibilidad

                    </h2>


                    <p className="text-xs text-gray-400 mt-1 uppercase tracking-widest font-bold">

                        Vacaciones, bajas médicas y permisos del personal

                    </p>


                </div>



                <button

                    onClick={()=>setShowCreate(true)}

                    className="bg-[#148F77] hover:bg-[#0f6b59] text-white px-6 py-3 rounded-2xl font-black text-xs uppercase tracking-wider transition-all shadow-md cursor-pointer"

                >

                    + Nueva Disponibilidad

                </button>


            </div>





            {/* FILTRO */}


            <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-5">


                <input


                    type="text"


                    placeholder="Buscar por personal o motivo..."


                    value={search}


                    onChange={(e)=>setSearch(e.target.value)}


                    className="w-full outline-none text-sm font-bold text-gray-700"

                />


            </div>






            {/* CONTENIDO */}


            {

                loading ?


                (

                    <div className="text-center py-16 text-gray-400 font-bold">

                        Cargando disponibilidades...

                    </div>

                )


                :


                filtered.length === 0 ?


                (

                    <div className="bg-white rounded-3xl p-12 text-center border border-gray-100">

                        <p className="text-sm font-black text-gray-500">

                            No existen disponibilidades registradas.

                        </p>

                    </div>

                )


                :


                (

                    <div className="overflow-auto bg-white rounded-3xl shadow-sm border border-gray-100">


                        <table className="min-w-full">


                            <thead className="bg-gray-50">


                                <tr className="text-xs uppercase text-gray-500">


                                    <th className="px-6 py-4 text-left">

                                        Personal

                                    </th>


                                    <th className="px-6 py-4 text-left">

                                        Motivo

                                    </th>


                                    <th className="px-6 py-4">

                                        Inicio

                                    </th>


                                    <th className="px-6 py-4">

                                        Fin

                                    </th>


                                    <th className="px-6 py-4">

                                        Estado

                                    </th>


                                    <th className="px-6 py-4">

                                        Acción

                                    </th>


                                </tr>


                            </thead>




                            <tbody>


                            {

                                filtered.map((d)=>{


                                    const fechaFin = new Date(d.fecha_fin);


                                    const hoy = new Date();


                                    hoy.setHours(0,0,0,0);



                                    const activa = fechaFin >= hoy;



                                    return (

                                        <tr

                                            key={d.id_disponibilidad}

                                            className="border-t border-gray-100 hover:bg-gray-50"

                                        >


                                            <td className="px-6 py-4 font-bold text-[#2A5C4D]">

                                                {d.nombre}

                                            </td>



                                            <td className="px-6 py-4">


                                                <span className="bg-emerald-50 text-[#148F77] border border-emerald-100 px-3 py-1 rounded-full text-xs font-black">

                                                    {d.motivo}

                                                </span>


                                            </td>




                                            <td className="px-6 py-4 text-center text-sm font-bold text-gray-600">

                                                {formatearFecha(d.fecha_inicio)}

                                            </td>




                                            <td className="px-6 py-4 text-center text-sm font-bold text-gray-600">

                                                {formatearFecha(d.fecha_fin)}

                                            </td>





                                            <td className="px-6 py-4 text-center">


                                                {

                                                    activa ?


                                                    (

                                                        <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-black">

                                                            Activa

                                                        </span>

                                                    )


                                                    :


                                                    (

                                                        <span className="bg-gray-200 text-gray-600 px-3 py-1 rounded-full text-xs font-black">

                                                            Finalizada

                                                        </span>

                                                    )

                                                }


                                            </td>





                                            <td className="px-6 py-4 text-center">


                                                <button

                                                    onClick={()=>eliminar(d.id_disponibilidad)}

                                                    className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-xl text-xs font-black cursor-pointer"

                                                >

                                                    Eliminar

                                                </button>


                                            </td>


                                        </tr>


                                    );


                                })


                            }


                            </tbody>



                        </table>


                    </div>


                )


            }






            {

                showCreate &&


                (

                    <FormDisponibilidad

                        onClose={()=>setShowCreate(false)}

                        onSuccess={()=>{


                            setShowCreate(false);


                            fetchDisponibilidad();


                        }}

                    />

                )


            }




        </div>

    );


}