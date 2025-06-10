import jwt from 'jsonwebtoken';
import { prisma } from '../index.js';

export const auth = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({ message: 'Authentication required' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await prisma.user.findUnique({
      where: { id: decoded.id }
    });

    if (!user) {
      return res.status(401).json({ message: 'Invalid authentication' });
    }

    req.user = user;
    req.token = token;
    next();
  } catch (error) {
    res.status(401).json({ message: 'Please authenticate' });
  }
};

export const authAdmin = async (req, res, next) => {
  try {
    await auth(req, res, () => {
      if (req.user.role !== 'ADMIN') {
        return res.status(403).json({ message: 'Admin access required' });
      }
      next();
    });
  } catch (error) {
    res.status(401).json({ message: 'Admin authentication failed' });
  }
}; 