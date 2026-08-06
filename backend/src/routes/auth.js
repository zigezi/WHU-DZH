import { Router } from 'express';
import crypto from 'node:crypto';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import svgCaptcha from 'svg-captcha';
import { pool } from '../db.js';

const router = Router();

const captchaStore = new Map();
const CAPTCHA_TTL = 5 * 60 * 1000;
const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-me';

function saveCaptcha(text) {
  const id = crypto.randomUUID();
  captchaStore.set(id, { text: text.toLowerCase(), expiresAt: Date.now() + CAPTCHA_TTL });
  return id;
}

function verifyCaptcha(id, input) {
  if (!id || !input) return false;
  const entry = captchaStore.get(id);
  if (!entry) return false;
  captchaStore.delete(id);
  if (Date.now() > entry.expiresAt) return false;
  return entry.text === String(input).trim().toLowerCase();
}

router.get('/captcha', (_req, res) => {
  const captcha = svgCaptcha.create({ size: 4, noise: 3, ignoreChars: '0o1ilI', color: true });
  const id = saveCaptcha(captcha.text);
  res.json({ id, svg: captcha.data });
});

router.post('/auth/register', async (req, res) => {
  const { username, email, password, captchaId, captcha } = req.body || {};
  if (!verifyCaptcha(captchaId, captcha)) {
    return res.status(400).json({ message: '验证码错误或已过期' });
  }
  if (!username || !email || !password) {
    return res.status(400).json({ message: '请填写完整的注册信息' });
  }
  if (!/^[a-zA-Z0-9_]{3,20}$/.test(username)) {
    return res.status(400).json({ message: '用户名需为3-20位字母、数字或下划线' });
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ message: '邮箱格式不正确' });
  }
  if (password.length < 6) {
    return res.status(400).json({ message: '密码至少6位' });
  }
  try {
    const exists = await pool.query('SELECT 1 FROM users WHERE username=$1 OR email=$2', [username, email]);
    if (exists.rowCount > 0) {
      return res.status(409).json({ message: '用户名或邮箱已存在' });
    }
    const hash = await bcrypt.hash(password, 10);
    const result = await pool.query(
      'INSERT INTO users (username, email, password) VALUES ($1,$2,$3) RETURNING id, username, email, created_at',
      [username, email, hash],
    );
    const token = jwt.sign({ id: result.rows[0].id, username }, JWT_SECRET, { expiresIn: '7d' });
    res.status(201).json({ message: '注册成功', token, user: result.rows[0] });
  } catch (err) {
    console.error('register error:', err);
    res.status(500).json({ message: '服务器错误' });
  }
});

router.post('/auth/login', async (req, res) => {
  const { username, password, captchaId, captcha } = req.body || {};
  if (!verifyCaptcha(captchaId, captcha)) {
    return res.status(400).json({ message: '验证码错误或已过期' });
  }
  if (!username || !password) {
    return res.status(400).json({ message: '请填写用户名和密码' });
  }
  try {
    const result = await pool.query(
      'SELECT id, username, email, password FROM users WHERE username=$1 OR email=$1',
      [username],
    );
    if (result.rowCount === 0) {
      return res.status(401).json({ message: '用户名或密码错误' });
    }
    const user = result.rows[0];
    const ok = await bcrypt.compare(password, user.password);
    if (!ok) {
      return res.status(401).json({ message: '用户名或密码错误' });
    }
    const token = jwt.sign({ id: user.id, username: user.username }, JWT_SECRET, { expiresIn: '7d' });
    res.json({ message: '登录成功', token, user: { id: user.id, username: user.username, email: user.email } });
  } catch (err) {
    console.error('login error:', err);
    res.status(500).json({ message: '服务器错误' });
  }
});

router.get('/auth/me', authenticate, async (req, res) => {
  res.json({ user: { id: req.user.id, username: req.user.username } });
});

export { captchaStore, JWT_SECRET };

export function authenticate(req, res, next) {
  const auth = req.headers.authorization || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : null;
  if (!token) return res.status(401).json({ message: '未登录' });
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ message: '登录已过期' });
  }
}

export default router;