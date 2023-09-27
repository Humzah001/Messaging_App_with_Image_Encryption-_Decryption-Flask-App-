CREATE DATABASE systemtool;

USE systemtool;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(255) ,
    Email VARCHAR(255) ,
    Description varchar(300) ,
    role ENUM('user', 'admin')
);


CREATE TABLE message(
    messageid INT AUTO_INCREMENT PRIMARY KEY,
    content text NOT NULL,
    Date datetime NOT NULL,
    receiverid Int,
    senderid Int,
    img longtext,
    foreign key (receiverid) references users(id),
    foreign key (senderid) references users(id)
);

CREATE TABLE report(
    reportid INT AUTO_INCREMENT PRIMARY KEY,
    Description text NOT NULL,
    id Int,
    foreign key (id) references users(id)
);

INSERT INTO `systemtool`.`users` (`username`, `password`, `role`) VALUES ('admin', 'admin', 'admin');

