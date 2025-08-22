// we are overriding the default epxress request object here

declare namespace Express {
    interface Request {
        userId?: string
    }
}