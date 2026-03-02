# Tattoo Booking MVP

MVP para una web de tatuadora con:
- Ver disponibilidad por día (slots de 15 min)
- Apartar un slot temporalmente (HOLD) sin cuentas
- Pagar anticipo fijo **$500 MXN** con Stripe (modo test)
- Confirmación automática vía webhook de Stripe

> Stack: Frontend (Vite + React) / Backend (FastAPI) / DB (PostgreSQL) / ORM (SQLAlchemy) / Migraciones (Alembic) / Docker Compose

---

## Decisión clave: garantía de “no solapamientos”
Este proyecto **NO usa** rangos (`tstzrange`) ni `EXCLUDE USING gist`.

En su lugar:
- Tabla `time_slots` con **una fila por `start_at`** (UTC) y `status`:
  - `FREE`: disponible
  - `HELD`: apartado temporalmente (`hold_expires_at`)
  - `BOOKED`: reservado/pagado
- `start_at` es **UNIQUE**, así que solo existe un slot por start time.

### Cómo se reserva sin solapamientos
1. El cliente elige un `start_at` (UTC) reportado como disponible.
2. El backend intenta un cambio atómico:
   - `UPDATE time_slots SET status='HELD' ... WHERE start_at=:start_at AND status='FREE'`
   - Si `rowcount == 1` => slot obtenido.
   - Si `rowcount == 0` => slot ya tomado (409).
3. Se crea un `booking` apuntando a `time_slot_id`.
4. Se crea un `PaymentIntent` de Stripe por **500 MXN**.
5. Webhook `payment_intent.succeeded` confirma:
   - `time_slots.HELD -> BOOKED`
   - `bookings -> CONFIRMED`

### Expiración de HOLD
- Si un slot está `HELD` y `hold_expires_at < now()`:
  - se revierte a `FREE`
  - y su booking (si estaba `HOLD` o `PENDING_PAYMENT`) pasa a `EXPIRED`

La expiración se ejecuta “oportunistamente” al entrar a endpoints clave.

---

## Requisitos
- Docker Desktop
- (Opcional) Node 20+ si quieres correr frontend fuera de Docker

---

## Configuración (.env)
**No subas llaves reales al repo.** Mantén `backend/.env` y `frontend/.env` fuera de Git (en `.gitignore`).

### Backend (`backend/.env`)
Ejemplo:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/tattoo
JWT_SECRET=change_me_to_a_long_random_string

# Stripe (test)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

