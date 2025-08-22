"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const middleware_1 = require("./middleware");
const index_1 = require("../../packages/db/src/index");
const cors_1 = __importDefault(require("cors"));
const app = (0, express_1.default)();
app.use((0, cors_1.default)());
app.use(express_1.default.json());
app.use(middleware_1.authMiddleware);
// to create website
app.post("/api/v1/website", async (req, res) => {
    const userId = req.userId;
    const { url } = req.body;
    const data = await index_1.client.website.create({
        data: {
            userId,
            url
        }
    });
    res.json({
        id: data.id
    });
});
// ticks of the website
app.get("/api/v1/website/status", async (req, res) => {
    const websiteId = req.query.websiteId;
    const userId = req.userId;
    const data = await index_1.client.website.findFirst({
        where: {
            id: websiteId,
            userId,
            disabled: false
        },
        include: {
            ticks: true
        }
    });
    res.json(data);
});
// all the websites that you currently have active
app.get("/api/v1/websites", async (req, res) => {
    const userId = req.userId;
    const websites = await index_1.client.website.findMany({
        where: {
            userId,
            disabled: false
        },
        include: {
            ticks: true
        }
    });
    res.json({ websites });
});
app.delete("/api/v1/website/", async (req, res) => {
    const websiteId = req.body.websiteId;
    const userId = req.userId;
    await index_1.client.website.update({
        where: {
            id: websiteId,
            userId
        },
        data: {
            disabled: true
        }
    });
    res.json({
        message: "Deleted website successfully"
    });
});
app.listen(8080);
