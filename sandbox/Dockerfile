FROM node:22.9.0-alpine

COPY . /sandbox

WORKDIR /sandbox

RUN npm install

EXPOSE 9000

CMD ["npm", "start"]
