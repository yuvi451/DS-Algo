"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.authMiddleware = authMiddleware;
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const config_1 = require("./config");
function authMiddleware(req, res, next) {
    const token = req.headers['authorization'];
    if (!token) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    const decoded = jsonwebtoken_1.default.verify(token, config_1.JWT_PUBLIC_KEY);
    console.log(decoded);
    // .sub is the userid of the user
    if (!decoded || !decoded.sub) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    req.userId = decoded.sub;
    next();
}
