import express from "express"
import { authMiddleware } from "./middleware"
import { client } from "../../packages/db/src/index"
import cors from "cors"

const app = express()
app.use(cors())
app.use(express.json())
app.use(authMiddleware)

// to create website
app.post("/api/v1/website", async (req, res) => {
    const userId = req.userId!
    const { url } = req.body

    const data = await client.website.create({
        data:{
            userId,
            url
        }
    })

    res.json({
        id: data.id
    })
})

// ticks of the website
app.get("/api/v1/website/status", async (req, res) => {
    const websiteId = req.query.websiteId as unknown as string
    const userId = req.userId!
    
    const data = await client.website.findFirst({
        where: {
            id: websiteId,
            userId,
            disabled: false
        },
        include: {
            ticks: true
        }
    })

    res.json(data)
})

// all the websites that you currently have active
app.get("/api/v1/websites", async (req, res) => {
    const userId = req.userId!

    const websites = await client.website.findMany({
        where: {
            userId,
            disabled: false
        },
        include : {
            ticks: true
        }
    })

    res.json({websites})
})

app.delete("/api/v1/website/", async (req, res) => {
    const websiteId = req.body.websiteId
    const userId = req.userId!

    await client.website.update({
        where: {
            id: websiteId,
            userId
        }, 
        data: {
            disabled: true
        }
    })

    res.json({
        message: "Deleted website successfully"
    })
})

app.listen(8080)



