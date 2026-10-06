const express = require('express');
const fs = require('fs');
const path = require('path');
const jwt = require('jsonwebtoken');

const app = express();
const port = 8080;
const filepath = path.join(__dirname, 'students.json');
const JWT_SECRET = 'secret-key';

const USERS = [
  { username: 'alice', password: 'pass123', role: 'user' },
  { username: 'admin', password: 'admin123', role: 'admin' }
];

let rentalsJSON = { rentals: [] };

function loadRentalsFile() {
  if (!fs.existsSync(filepath)) {
    fs.writeFileSync(filepath, JSON.stringify({ rentals: [] }));
  }

  const raw = fs.readFileSync(filepath, 'utf8');
  const parsed = JSON.parse(raw || '{}');

  if (Array.isArray(parsed)) {
    rentalsJSON = { rentals: parsed };
  } else if (Array.isArray(parsed.rentals)) {
    rentalsJSON = { rentals: parsed.rentals };
  } else if (Array.isArray(parsed.students)) {
    rentalsJSON = { rentals: parsed.students };
  } else {
    rentalsJSON = { rentals: [] };
  }

  fs.writeFileSync(filepath, JSON.stringify(rentalsJSON));
}

loadRentalsFile();

app.use(express.json());
app.use(express.static(path.join(__dirname, 'frontend')));

function verifyToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Missing token' });
  }

  jwt.verify(token, JWT_SECRET, (err, payload) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid or expired token' });
    }
    req.user = payload;
    next();
  });
}

function requireAdmin(req, res, next) {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Admin role required' });
  }
  next();
}

app.get('/', (req, res) => {
  res.send('Lab Assignment 1!');
});

app.get('/rentals', (req, res) => {
  res.json(rentalsJSON.rentals);
});

app.post('/newrental', (req, res) => {
  const rental = req.body;

  if (!rental || typeof rental !== 'object') {
    return res.status(400).json({ error: 'Invalid rental payload' });
  }

  rentalsJSON.rentals.push(rental);
  fs.writeFileSync(filepath, JSON.stringify(rentalsJSON));
  res.status(201).end();
});

app.post('/login', (req, res) => {
  const { username, password } = req.body;
  const user = USERS.find(u => u.username === username && u.password === password);

  if (!user) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  const token = jwt.sign(
    { username: user.username, role: user.role },
    JWT_SECRET,
    { expiresIn: '1h' }
  );

  res.json({ token });
});

app.get('/studentsv', verifyToken, (req, res) => {
  res.json({ rentals: rentalsJSON.rentals });
});

app.post('/newstudentv', verifyToken, requireAdmin, (req, res) => {
  const rental = req.body;

  if (!rental || typeof rental !== 'object') {
    return res.status(400).json({ error: 'Invalid student payload' });
  }

  rentalsJSON.rentals.push(rental);
  fs.writeFileSync(filepath, JSON.stringify(rentalsJSON));
  res.status(201).end();
});

app.listen(port, () => {
  console.log(`PTI HTTP Server listening at http://localhost:${port}`);
});


