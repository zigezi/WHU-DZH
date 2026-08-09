import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import authRouter from './routes/auth.js';
import sessionsRouter from './routes/sessions.js';
import buildRouter, { previewRouter } from './routes/build.js';
import containerRouter from './routes/container.js';
import { initDb } from './db.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();

app.use(cors());
app.use(express.json());

app.use('/api', authRouter);
// buildRouter（含 query/cookie token 鉴权）必须先于 sessionsRouter 挂载，否则
// sessionsRouter 的全局 header-only authenticate 会把 /api/*?token= 提前 401 掉。
app.use('/api', buildRouter);
app.use('/api', containerRouter);
app.use('/api', sessionsRouter);
app.use('/preview', previewRouter);

const dist = path.join(__dirname, '../../frontend/dist');
app.use(express.static(dist));
app.get(/^\/(?!api)(?!preview).*/, (_req, res) => {
  res.sendFile(path.join(dist, 'index.html'));
});

const PORT = process.env.PORT || 3000;

initDb()
  .then(() => {
    app.listen(PORT, '0.0.0.0', () => {
      console.log(`Server running on http://0.0.0.0:${PORT}`);
    });
  })
  .catch((err) => {
    console.error('DB init failed:', err);
    process.exit(1);
  });