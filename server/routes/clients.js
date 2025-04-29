import express from 'express';
import { prisma } from '../index.js';
import { auth } from '../middlewares/auth.js';

const router = express.Router();

// Get all clients
router.get('/', auth, async (req, res) => {
  try {
    const clients = await prisma.client.findMany({
      orderBy: { 
        createdAt: 'desc' 
      }
    });
    
    res.json(clients);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Get client by ID
router.get('/:id', auth, async (req, res) => {
  try {
    const client = await prisma.client.findUnique({
      where: { id: req.params.id },
      include: {
        tickets: {
          orderBy: {
            createdAt: 'desc'
          }
        }
      }
    });
    
    if (!client) {
      return res.status(404).json({ message: 'Client not found' });
    }
    
    res.json(client);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Create client
router.post('/', auth, async (req, res) => {
  try {
    const { name, email, phone, address } = req.body;
    
    // Check if client with this email already exists
    const existingClient = await prisma.client.findUnique({
      where: { email }
    });
    
    if (existingClient) {
      return res.status(400).json({ message: 'Client with this email already exists' });
    }
    
    const client = await prisma.client.create({
      data: {
        name,
        email,
        phone,
        address
      }
    });
    
    res.status(201).json(client);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Update client
router.put('/:id', auth, async (req, res) => {
  try {
    const { name, email, phone, address } = req.body;
    
    const client = await prisma.client.update({
      where: { id: req.params.id },
      data: {
        name,
        email,
        phone,
        address
      }
    });
    
    res.json(client);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Delete client
router.delete('/:id', auth, async (req, res) => {
  try {
    await prisma.client.delete({
      where: { id: req.params.id }
    });
    
    res.json({ message: 'Client deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

export default router; 