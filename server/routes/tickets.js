import express from 'express';
import { prisma } from '../index.js';
import { auth } from '../middlewares/auth.js';

const router = express.Router();

// Get all tickets
router.get('/', auth, async (req, res) => {
  try {
    const { status, priority, clientId, assignedToId } = req.query;
    
    const filters = {};
    if (status) filters.status = status;
    if (priority) filters.priority = priority;
    if (clientId) filters.clientId = clientId;
    if (assignedToId) filters.assignedToId = assignedToId;
    
    const tickets = await prisma.ticket.findMany({
      where: filters,
      include: {
        client: {
          select: {
            id: true,
            name: true,
            email: true
          }
        },
        assignedTo: {
          select: {
            id: true,
            name: true
          }
        },
        createdBy: {
          select: {
            id: true,
            name: true
          }
        }
      },
      orderBy: {
        updatedAt: 'desc'
      }
    });
    
    res.json(tickets);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Get ticket by ID
router.get('/:id', auth, async (req, res) => {
  try {
    const ticket = await prisma.ticket.findUnique({
      where: { id: req.params.id },
      include: {
        client: true,
        assignedTo: {
          select: {
            id: true,
            name: true,
            email: true
          }
        },
        createdBy: {
          select: {
            id: true,
            name: true
          }
        },
        comments: {
          orderBy: {
            createdAt: 'asc'
          }
        }
      }
    });
    
    if (!ticket) {
      return res.status(404).json({ message: 'Ticket not found' });
    }
    
    res.json(ticket);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Create ticket
router.post('/', auth, async (req, res) => {
  try {
    const { title, description, clientId, priority, assignedToId } = req.body;
    
    const ticket = await prisma.ticket.create({
      data: {
        title,
        description,
        priority: priority || 'MEDIUM',
        clientId,
        assignedToId,
        createdById: req.user.id
      },
      include: {
        client: {
          select: {
            id: true,
            name: true,
            email: true
          }
        },
        assignedTo: {
          select: {
            id: true,
            name: true
          }
        },
        createdBy: {
          select: {
            id: true,
            name: true
          }
        }
      }
    });
    
    res.status(201).json(ticket);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Update ticket
router.put('/:id', auth, async (req, res) => {
  try {
    const { title, description, status, priority, assignedToId } = req.body;
    
    const ticket = await prisma.ticket.update({
      where: { id: req.params.id },
      data: {
        title,
        description,
        status,
        priority,
        assignedToId
      },
      include: {
        client: {
          select: {
            id: true,
            name: true,
            email: true
          }
        },
        assignedTo: {
          select: {
            id: true,
            name: true
          }
        }
      }
    });
    
    res.json(ticket);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Delete ticket
router.delete('/:id', auth, async (req, res) => {
  try {
    await prisma.ticket.delete({
      where: { id: req.params.id }
    });
    
    res.json({ message: 'Ticket deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Add comment to ticket
router.post('/:id/comments', auth, async (req, res) => {
  try {
    const { content } = req.body;
    
    const comment = await prisma.comment.create({
      data: {
        content,
        ticketId: req.params.id
      }
    });
    
    res.status(201).json(comment);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Update comment
router.put('/comments/:id', auth, async (req, res) => {
  try {
    const { content } = req.body;
    
    const comment = await prisma.comment.update({
      where: { id: req.params.id },
      data: { content }
    });
    
    res.json(comment);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Delete comment
router.delete('/comments/:id', auth, async (req, res) => {
  try {
    await prisma.comment.delete({
      where: { id: req.params.id }
    });
    
    res.json({ message: 'Comment deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

export default router; 