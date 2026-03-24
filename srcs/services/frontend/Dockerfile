FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

EXPOSE 3001 8788

CMD ["npm", "run", "dev:next"]
