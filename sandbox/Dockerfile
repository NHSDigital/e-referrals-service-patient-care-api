FROM node:24.2.0-alpine

COPY . /sandbox

WORKDIR /sandbox

RUN npm install

EXPOSE 9000

CMD ["npm", "start"]
