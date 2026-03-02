import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { Routes, Route, NavLink, useNavigate } from "react-router-dom";
import { loadStripe } from "@stripe/stripe-js";
import { Elements, PaymentElement, useElements, useStripe } from "@stripe/react-stripe-js";

// Fotos
import work1 from "./assets/portfolio/work1.jpg";
import work2 from "./assets/portfolio/work2.jpg";
import work3 from "./assets/portfolio/work3.jpg";
import work4 from "./assets/portfolio/work4.jpg";
import studio from "./assets/portfolio/work5.jpg";
import work6 from "./assets/portfolio/work6.jpg";
import work7 from "./assets/portfolio/work7.jpg";
import work8 from "./assets/portfolio/work8.jpg";
import work9 from "./assets/portfolio/work9.jpg";
import work10 from "./assets/portfolio/work10.jpg";


const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const STRIPE_PK = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;
const stripePromise = STRIPE_PK ? loadStripe(STRIPE_PK) : null;

const GALLERY = [
  { src: work1, alt: "Trabajo 1" },
  { src: work2, alt: "Trabajo 2" },
  { src: work3, alt: "Trabajo 3" },
  { src: work4, alt: "Trabajo 4" },
  { src: studio, alt: "Trabajo 5" },
  { src: work6, alt: "Trabajo 6" },
  { src: work7, alt: "Trabajo 7" },
  { src: work8, alt: "Trabajo 8" },
  { src: work9, alt: "Trabajo 9" },
  { src: work10, alt: "Trabajo 10" },
];

function Topbar() {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="logoDot" />
        <div>
          <div className="brandTitle">Tatuajes De Doris</div>
          <div className="brandSub">Tatuajes • Agenda • Anticipo</div>
        </div>
      </div>

      <nav className="topActions">
        <NavLink to="/" className={({ isActive }) => (isActive ? "navLink navLinkActive" : "navLink")}>
          Inicio
        </NavLink>
        <NavLink to="/galeria" className={({ isActive }) => (isActive ? "navLink navLinkActive" : "navLink")}>
          Galería
        </NavLink>
        <NavLink to="/agendar" className={({ isActive }) => (isActive ? "navLink navLinkActive" : "navLink")}>
          Agendar
        </NavLink>
      </nav>
    </header>
  );
}

function PageShell({ children }) {
  return (
    <div>
      <Topbar />
      <main className="shellOne">{children}</main>
    </div>
  );
}

/* -------------------- Home -------------------- */

function HomePage() {
  const nav = useNavigate();

  return (
    <PageShell>
      <section className="card heroCard">
        <div className="heroLeft">
          <div className="pill">Doris Pufleau</div>

          <h1 className="heroTitle">Tatuajes Full Color y estilo Parche</h1>

          <p className="heroLead">
            Agenda tu cita en línea y asegura tu horario con un anticipo fijo de <b>$500 MXN</b>.
          </p>

          <div className="heroStats">
            <div className="stat">
              <div className="statNum">15 min</div>
              <div className="statLabel">Slots</div>
            </div>
            <div className="stat">
              <div className="statNum">$500</div>
              <div className="statLabel">Anticipo</div>
            </div>
            <div className="stat">
              <div className="statNum">Rápido</div>
              <div className="statLabel">Confirmación</div>
            </div>
          </div>

          <div className="btnRow">
            <button className="primaryBtn" onClick={() => nav("/agendar")}>
              Agendar ahora
            </button>
            <button className="secondaryBtn" onClick={() => nav("/galeria")}>
              Ver galería
            </button>
          </div>

                <div className="subtle heroContact">
                  <b>WhatsApp:</b> +52 33 1444 3402 <br />
                  <b>Zona:</b> Zapopan / GDL <br />
                  <b>Instagram:</b> @tatuajesdedoris
                </div>
        </div>

        <div className="heroImgWrap">
          <img src={studio} alt="Estudio" className="heroImg" />
        </div>
      </section>

      <section className="card" style={{ padding: 18, marginTop: 16 }}>
        <h2 style={{ marginTop: 0 }}>Sobre mi</h2>
        <p style={{ margin: 0, lineHeight: 1.7, color: "rgba(15,23,42,0.78)" }}>
        Mi nombre es Doris. Me especializo en tatuaje estilo bordado y full color, con un enfoque en color sólido, detalles limpios y una experiencia cómoda y profesional. Llevo 3 años tatuando y actualmente trabajo en el estudio Pink Devil Club. Si quieres agendar, puedes seleccionar tu horario y asegurar tu cita con un anticipo de $500 MXN.
        </p>
      </section>

      <section style={{ marginTop: 18 }}>
        <div className="sectionTitleRow">
          <h2 style={{ margin: 0, color: "white" }}>Preview de galería</h2>
          <span className="sectionHint">Un vistazo rápido</span>
        </div>

        <div className="galleryGrid">
          {GALLERY.map((g) => (
            <div className="galleryItem" key={g.alt}>
              <img src={g.src} alt={g.alt} className="galleryImg" />
            </div>
          ))}
        </div>
      </section>
    </PageShell>
  );
}

/* -------------------- Gallery -------------------- */

function GalleryPage() {
  return (
    <PageShell>
      <div className="sectionTitleRow">
        <h1 style={{ margin: 0, color: "white" }}>Galería</h1>
        <span className="sectionHint">Trabajos recientes</span>
      </div>

      <div className="galleryGrid">
        {GALLERY.map((g) => (
          <div className="galleryItem" key={g.alt}>
            <img src={g.src} alt={g.alt} className="galleryImg" />
          </div>
        ))}
      </div>

      <div className="card" style={{ padding: 18, marginTop: 16 }}>
        <h3 style={{ marginTop: 0 }}>Contacto</h3>
        <div style={{ color: "rgba(15,23,42,0.78)", lineHeight: 1.7 }}>
          WhatsApp: <b>+52 33 1444 3402</b> <br />
          Zona: <b>Zapopan / GDL</b> <br />
          Instagram: <b>@tatuajesdedoris</b>
        </div>
      </div>
    </PageShell>
  );
}

/* -------------------- Booking (Agendar) -------------------- */

function CheckoutForm({ bookingId, onPaid }) {
  const stripe = useStripe();
  const elements = useElements();
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMsg("");
    if (!stripe || !elements) return;

    setSubmitting(true);

    const { error, paymentIntent } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: window.location.href },
      redirect: "if_required",
    });

    if (error) {
      setMsg(error.message || "Ocurrió un error al procesar el pago.");
      setSubmitting(false);
      return;
    }

    if (paymentIntent?.status === "succeeded") setMsg("✅ Pago completado. Esperando confirmación…");
    else if (paymentIntent?.status === "processing") setMsg("Pago en procesamiento. Esperando confirmación…");
    else setMsg(`Pago enviado (status: ${paymentIntent?.status || "unknown"}).`);

    setSubmitting(false);
    onPaid?.();
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
      <div className="subtle">
        Anticipo fijo: <b>$500 MXN</b>
      </div>

      <div className="subtle subtlePay">
        <PaymentElement />
      </div>

      <button disabled={!stripe || submitting} className="primaryBtn" type="submit">
        {submitting ? "Procesando…" : "Pagar anticipo"}
      </button>

      {msg && <div style={{ fontSize: 14 }}>{msg}</div>}
      <div style={{ fontSize: 12, opacity: 0.75 }}>Booking ID: {bookingId}</div>
    </form>
  );
}

function BookingPage() {
  const [day, setDay] = useState(() => new Date().toISOString().slice(0, 10));
  const [slots, setSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slotsError, setSlotsError] = useState("");

  const [form, setForm] = useState({
    customer_name: "",
    customer_email: "",
    customer_phone: "",
    description: "",
  });

  const [selectedStartAt, setSelectedStartAt] = useState("");
  const [booking, setBooking] = useState(null);
  const [clientSecret, setClientSecret] = useState("");
  const [statusMsg, setStatusMsg] = useState("");

  const elementsOptions = useMemo(() => {
    if (!clientSecret) return null;
    return { clientSecret, appearance: { theme: "stripe" } };
  }, [clientSecret]);

  async function fetchAvailability() {
    setLoadingSlots(true);
    setSlotsError("");
    try {
      const res = await fetch(`${API_BASE}/availability?day=${day}`);
      if (!res.ok) throw new Error(`Availability error (${res.status})`);
      const data = await res.json();
      setSlots(data.slots || []);
    } catch (e) {
      setSlots([]);
      setSlotsError(e.message || "Error loading availability");
    } finally {
      setLoadingSlots(false);
    }
  }

  useEffect(() => {
    fetchAvailability();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [day]);

  async function createHold() {
    setStatusMsg("");
    setClientSecret("");
    setBooking(null);

    if (!selectedStartAt) return setStatusMsg("Elige un horario primero.");
    if (!form.customer_name || !form.customer_email || !form.customer_phone)
      return setStatusMsg("Completa nombre, email y teléfono.");

    const payload = { start_at: selectedStartAt, ...form };

    try {
      const res = await fetch(`${API_BASE}/bookings/hold`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) return setStatusMsg(data?.detail || `Hold error (${res.status})`);

      setBooking(data);
      setStatusMsg(`Slot apartado. Expira: ${data.hold_expires_at}`);
      fetchAvailability();
    } catch (e) {
      setStatusMsg(e.message || "Error creating hold");
    }
  }

  async function createPaymentIntent() {
    setStatusMsg("");
    if (!booking?.id) return setStatusMsg("Primero crea el hold.");

    try {
      const res = await fetch(`${API_BASE}/payments/intent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ booking_id: booking.id }),
      });
      const data = await res.json();
      if (!res.ok) return setStatusMsg(data?.detail || `Payment intent error (${res.status})`);

      setClientSecret(data.client_secret);
      setStatusMsg("Pago listo. Completa el anticipo.");
    } catch (e) {
      setStatusMsg(e.message || "Error creating payment intent");
    }
  }

  function startPollingBooking(id) {
    let tries = 0;
    const t = setInterval(async () => {
      tries += 1;
      try {
        const res = await fetch(`${API_BASE}/bookings/${id}`);
        if (res.ok) {
          const data = await res.json();
          setBooking(data);
          if (data.status === "CONFIRMED") {
            setStatusMsg("✅ Cita confirmada. ¡Nos vemos pronto!");
            clearInterval(t);
          }
          if (data.status === "EXPIRED") {
            setStatusMsg("⏳ El hold expiró. Vuelve a elegir un horario.");
            clearInterval(t);
          }
        }
      } catch {}
      if (tries >= 12) clearInterval(t);
    }, 2000);
  }

  const canPay = Boolean(clientSecret && stripePromise && elementsOptions);

  return (
    <PageShell>
      <section className="card panel">
        <div className="panelHeader">
          <div>
            <div style={{ fontWeight: 900, fontSize: 18 }}>Agendar cita</div>
            <div style={{ fontSize: 12, opacity: 0.75 }}>
              Elige día y horario (UTC) y aparta tu slot.
            </div>
          </div>
          <button onClick={fetchAvailability} className="secondaryBtn" type="button">
            Refrescar
          </button>
        </div>

        <div className="grid2">
          <label className="label">
            Día:
            <input className="input" type="date" value={day} onChange={(e) => setDay(e.target.value)} />
          </label>

          <div className="subtle" style={{ display: "grid", alignContent: "center", gap: 4 }}>
            <div style={{ fontSize: 12, opacity: 0.75 }}>Estado</div>
            <div style={{ fontWeight: 800 }}>
              {booking ? `Booking #${booking.id} (${booking.status})` : "Sin booking"}
            </div>
          </div>
        </div>

        {/* Desktop layout 2 columnas */}
        <div className="bookingGrid">
          {/* Izquierda: horarios */}
          <div>
            <div style={{ marginTop: 12 }}>
              <div style={{ fontWeight: 900, marginBottom: 8 }}>Horarios disponibles</div>

              {loadingSlots && <div className="subtle">Cargando…</div>}
              {slotsError && <div style={{ color: "#c02626" }}>{slotsError}</div>}
              {!loadingSlots && !slotsError && slots.length === 0 && (
                <div className="subtle">No hay slots disponibles.</div>
              )}

              <div className="slotGrid">
                {slots.map((s) => {
                  const isSelected = selectedStartAt === s.start_at;
                  return (
                    <button
                      key={s.start_at}
                      className={`slotBtn ${isSelected ? "slotBtnSelected" : ""}`}
                      onClick={() => setSelectedStartAt(s.start_at)}
                      type="button"
                    >
                      {new Date(s.start_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} (UTC)
                    </button>
                  );
                })}
              </div>

              {selectedStartAt && (
                <div className="subtle" style={{ marginTop: 10 }}>
                  Seleccionado: <b>{selectedStartAt}</b>
                </div>
              )}
            </div>
          </div>

          {/* Derecha: datos + pago */}
          <div>
            <div className="hr" />

            <div style={{ display: "grid", gap: 10 }}>
              <div style={{ fontWeight: 900 }}>Datos del cliente</div>

              <div className="grid2">
                <input
                  className="input"
                  placeholder="Nombre"
                  value={form.customer_name}
                  onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Teléfono"
                  value={form.customer_phone}
                  onChange={(e) => setForm({ ...form, customer_phone: e.target.value })}
                />
              </div>

              <input
                className="input"
                placeholder="Email"
                value={form.customer_email}
                onChange={(e) => setForm({ ...form, customer_email: e.target.value })}
              />

              <textarea
                className="input"
                placeholder="Descripción (opcional)"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                style={{ minHeight: 90 }}
              />

              <div className="btnRow">
                <button onClick={createHold} className="primaryBtn" type="button">
                  Apartar (HOLD)
                </button>
                <button
                  onClick={createPaymentIntent}
                  className="secondaryBtn"
                  disabled={!booking?.id}
                  type="button"
                >
                  Preparar pago
                </button>
              </div>

              {statusMsg && <div style={{ fontSize: 14 }}>{statusMsg}</div>}

              {booking?.hold_expires_at && (
                <div className="subtle">
                  Tu hold expira en: <b>{booking.hold_expires_at}</b>
                </div>
              )}
            </div>

            {canPay && (
              <div style={{ marginTop: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
                  <h3 style={{ margin: 0, fontSize: 16 }}>Pago de anticipo</h3>
                  <span style={{ fontSize: 12, opacity: 0.75 }}>Tarjeta test: 4242 4242 4242 4242</span>
                </div>

                <Elements stripe={stripePromise} options={elementsOptions}>
                  <CheckoutForm bookingId={booking?.id} onPaid={() => startPollingBooking(booking.id)} />
                </Elements>
              </div>
            )}
          </div>
        </div>

        {!STRIPE_PK && (
          <div style={{ marginTop: 12, color: "#c02626" }}>
            Falta VITE_STRIPE_PUBLISHABLE_KEY (pk_test_...) en frontend/.env
          </div>
        )}
      </section>

      <div className="finePrint">
        <div style={{ fontWeight: 800, marginBottom: 6 }}>Política de anticipo</div>
        <div style={{ fontSize: 13, opacity: 0.88 }}>
          El anticipo asegura tu horario. Si necesitas reagendar, avisa con anticipación.
        </div>
      </div>
    </PageShell>
  );
}

/* -------------------- Router -------------------- */

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/galeria" element={<GalleryPage />} />
      <Route path="/agendar" element={<BookingPage />} />
      <Route path="*" element={<HomePage />} />
    </Routes>
  );
}