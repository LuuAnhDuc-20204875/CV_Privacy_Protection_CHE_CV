const express = require('express')
const fs = require('fs')
const https = require('https')
const http = require('http')
const cors = require("cors")

const app = express();
app.use(cors());
const options = {
key: fs.readFileSync('cert/privatekey.key'),
cert: fs.readFileSync('cert/certificate.crt')
};
const server = https.createServer(options, app);
// app.use(express.static("static"));
app.use(express.static("PaddleOCR"));


server.listen(9000, () => { // set up domain
console.log('listening on port 9000');
});



// import express from 'express';
// import fs from 'fs';
// import https from 'https';
// import cors from 'cors';

// const app = express();
// app.use(cors());

// const options = {
//   key: fs.readFileSync('cert/privatekey.key'),
//   cert: fs.readFileSync('cert/certificate.crt')
// };

// const server = https.createServer(options, app);
// app.use(express.static("static"));

// server.listen(9000, () => {
//   console.log('listening on port 9000');
// });
