FROM node:20-alpine

ARG NEXT_PUBLIC_API_URL=
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --loglevel verbose
COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
