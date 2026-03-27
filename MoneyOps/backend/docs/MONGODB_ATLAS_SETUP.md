# MongoDB Atlas Setup (Free, shareable with team)

The backend uses **MongoDB** so you can use **MongoDB Atlas** free tier: one shared database, no 30-day expiry, easy to share with teammates.

---

## 1. Create a free cluster

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) and sign up / log in.
2. **Create** a new project (e.g. "MoneyOps").
3. **Build a database** → choose **M0 FREE**.
4. Pick a cloud provider and region (closest to you).
5. Create cluster (takes 1–2 minutes).

---

## 2. Database user and network access

1. When prompted, create a **database user** (username + password). Save the password.
2. **Where would you like to connect from?** → **My Local Environment** (or add **0.0.0.0/0** for “allow from anywhere” for dev; lock this down in production).
3. Finish the wizard.

---

## 3. Get the connection string

1. In Atlas, click **Connect** on your cluster.
2. **Drivers** (or “Connect your application”) → copy the **connection string**.
   - It looks like: `mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`
3. Replace `<password>` with your database user password.
4. Add the database name (e.g. `moneyops`) before `?`:  
   `mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/moneyops?retryWrites=true&w=majority`

---

## 4. Configure the backend

Set the **MONGODB_URI** env var (or in `.env`):

```bash
MONGODB_URI=mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/moneyops?retryWrites=true&w=majority
```

**Local run (PowerShell):**

```powershell
$env:MONGODB_URI="mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/moneyops?retryWrites=true&w=majority"
cd C:\Projects\MoneyOps\MoneyOps\backend
mvn spring-boot:run
```

**Railway / other host:** add `MONGODB_URI` in the service Variables with the same value.

---

## 5. Share with team

- **Same URI:** share the connection string (with user/password) over a secure channel; everyone uses the same `MONGODB_URI`.
- **Or:** create a separate Atlas database user per teammate and give each their own URI (same cluster, same DB name `moneyops`).

Collections (tables) and documents are created automatically when the app runs. No manual schema steps.

---

## 6. Local MongoDB (optional)

Without Atlas, run MongoDB locally and leave `MONGODB_URI` unset (default in `application.yml` is `mongodb://localhost:27017/moneyops`):

- **Windows:** [MongoDB Community Server](https://www.mongodb.com/try/download/community) or Docker: `docker run -p 27017:27017 mongo`

---

## Summary

| Env var       | Example / default |
|----------------|--------------------|
| `MONGODB_URI`  | `mongodb+srv://...@cluster0.xxx.mongodb.net/moneyops?retryWrites=true&w=majority` or `mongodb://localhost:27017/moneyops` |

No MySQL/Railway env vars are used anymore; the app uses only MongoDB.
