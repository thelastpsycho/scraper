import pkg from 'whatsapp-web.js';
const { Client, LocalAuth } = pkg;
import express from 'express';
import axios from 'axios';
import qrcode from 'qrcode-terminal';
import dayjs from 'dayjs';

process.on('uncaughtException', err => {
  console.error('Uncaught Exception:', err);
});
process.on('unhandledRejection', err => {
  console.error('Unhandled Rejection:', err);
});

const app = express();
const PORT = 3001; // WhatsApp bot API port

// Helper: Map abbreviations to room types
const ROOM_ABBR = {
  BFS: 'Beach Front Private Suite Room',
  DLP: 'Deluxe Pool Access',
  DLX: 'Deluxe Room',
  DLS: 'Deluxe Suite Room',
  FPK: 'Family Premiere Room',
  PRE: 'Premiere Room',
  PKL: 'Premiere Room Lagoon Access',
  PRS: 'Premiere Suite Room',
  AVR: 'The Anvaya Residence',
  AVS: 'The Anvaya Suite No Pool',
  ASW: 'The Anvaya Suite Whirpool',
  ASP: 'The Anvaya Suite With Pool',
  AVP: 'The Anvaya Villa',
  'DLX+Pre': 'DLX+Pre',
};

// Helper: Parse user message like 'bfs 5-9 jul' or 'dlx 10-12 aug'
function parseUserQuery(text) {
  const match = text.match(/([a-zA-Z+]+)\s+(\d{1,2})-(\d{1,2})\s*([a-zA-Z]+)/);
  if (!match) return null;
  const abbr = match[1].toUpperCase();
  const startDay = parseInt(match[2], 10);
  const endDay = parseInt(match[3], 10);
  const monthStr = match[4];
  const month = dayjs().month(monthStr).month(); // e.g., 'jul' => 6 (July)
  if (isNaN(month)) return null;
  const year = dayjs().year();
  return { abbr, startDay, endDay, month, year };
}

// Helper: Format reply as plain text
function formatReply(roomAbbr, dates, values) {
  let lines = [`Room Type: ${roomAbbr}`];
  dates.forEach((date, i) => {
    lines.push(`${date}: ${values[i]}`);
  });
  return lines.join('\n');
}

// Start WhatsApp client
const client = new Client({
  authStrategy: new LocalAuth()
});

client.on('qr', (qr) => {
  qrcode.generate(qr, { small: true });
  console.log('Scan the QR code above with WhatsApp to authenticate.');
});

client.on('ready', () => {
  console.log('WhatsApp client is ready!');
});

client.on('auth_failure', msg => {
  console.error('AUTH FAILURE', msg);
});

client.on('disconnected', reason => {
  console.error('Client was logged out', reason);
});

client.on('error', err => {
  console.error('Client error', err);
});

client.on('message', async (msg) => {
  const chat = await msg.getChat();
  if (chat.isGroup) return; // Only respond to private chats
  const userMessage = msg.body.trim();
  const parsed = parseUserQuery(userMessage);
  if (!parsed) {
    await msg.reply('Please ask in the format: <room abbr> <startDay>-<endDay> <month>\nExample: bfs 5-9 jul');
    return;
  }
  const { abbr, startDay, endDay, month, year } = parsed;
  const roomType = ROOM_ABBR[abbr];
  if (!roomType) {
    await msg.reply('Unknown room abbreviation.');
    return;
  }
  try {
    // Fetch inventory data
    const res = await axios.get('http://localhost:8000/api/db/combined-inventory');
    const data = Array.isArray(res.data) ? res.data : (res.data?.data || []);
    // Filter for dates in range
    const dates = [];
    const values = [];
    for (let d = startDay; d <= endDay; d++) {
      const dateObj = dayjs().year(year).month(month).date(d);
      const dateStr = dateObj.format('YYYY-MM-DD');
      // Find row with matching date
      const row = data.find(row => {
        const dateKey = Object.keys(row).find(k => k.toLowerCase().includes('date'));
        if (!dateKey) return false;
        return dayjs(row[dateKey]).isSame(dateObj, 'day');
      });
      dates.push(dateObj.format('D MMM YYYY'));
      if (row && row[roomType] !== undefined) {
        values.push(row[roomType]);
      } else {
        values.push('N/A');
      }
    }
    const reply = formatReply(abbr, dates, values);
    await msg.reply(reply);
  } catch (err) {
    await msg.reply('Error checking availability.');
    console.error('Inventory API error:', err.message);
  }
});

// Optional: Express server for health check or webhook
app.get('/', (req, res) => {
  res.send('WhatsApp bot is running.');
});

app.listen(PORT, () => {
  console.log(`Express server running on http://localhost:${PORT}`);
});

client.initialize();

// To run: npm install && npm start 