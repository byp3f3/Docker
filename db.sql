CREATE TABLE category (
    categoryId INT PRIMARY KEY,
    categoryName VARCHAR(100) NOT NULL,
    categoryDescription TEXT NOT NULL
);

CREATE TABLE brand (
    brandId INT PRIMARY KEY,
    brandName VARCHAR(100) NOT NULL,
    brandDescription TEXT NOT NULL,
    brandCountry VARCHAR(100) NOT NULL
);

CREATE TABLE product (
    productId BIGINT PRIMARY KEY,
    productName VARCHAR(100) NOT NULL,
    productDescription TEXT NOT NULL,
    categoryId INT NOT NULL,
    brandId INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    ageRating INT NOT NULL,
    quantity INT NOT NULL,
    weightKg DECIMAL(10,2) NOT NULL,
    dimensions VARCHAR(50) NOT NULL,
    FOREIGN KEY (categoryId) REFERENCES category(categoryId),
    FOREIGN KEY (brandId) REFERENCES brand(brandId)
);

CREATE TABLE productImage (
    productImageId BIGINT PRIMARY KEY,
    productId BIGINT NOT NULL,
    url VARCHAR(500) NOT NULL,
    altText VARCHAR(100) NOT NULL,
    isMain BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (productId) REFERENCES product(productId)
);

CREATE TABLE productAttribute (
    productAttributeId BIGINT PRIMARY KEY,
    productId BIGINT NOT NULL,
    productAttributeName VARCHAR(100) NOT NULL,
    productAttributeValue VARCHAR(100) NOT NULL,
    productAttributeUnit VARCHAR(50),
    FOREIGN KEY (productId) REFERENCES product(productId)
);

CREATE TABLE "role" (
    roleId INT PRIMARY KEY,
    roleName VARCHAR(100) NOT NULL
);

CREATE TABLE "user" (
    userId BIGINT PRIMARY KEY,
    lastName VARCHAR(100) NOT NULL,
    firstName VARCHAR(100) NOT NULL,
    middleName VARCHAR(100),
    email VARCHAR(255) NOT NULL,
    password VARCHAR(100) NOT NULL,
    roleId INT NOT NULL,
    phone VARCHAR(11) NOT NULL,
    birthDate DATE NOT NULL,
    createdAt TIMESTAMP NOT NULL,
    FOREIGN KEY (roleId) REFERENCES "role"(roleId)
);

CREATE TABLE address (
    AddressId BIGINT PRIMARY KEY,
    userId BIGINT NOT NULL,
    city VARCHAR(100) NOT NULL,
    street VARCHAR(100) NOT NULL,
    house VARCHAR(50) NOT NULL,
    flat VARCHAR(10),
    index VARCHAR(6) NOT NULL,
    FOREIGN KEY (userId) REFERENCES "user"(userId)
);

CREATE TABLE review (
    reviewId BIGINT PRIMARY KEY,
    productId BIGINT NOT NULL,
    userId BIGINT NOT NULL,
    rating INT NOT NULL,
    reviewText TEXT,
    createdAt TIMESTAMP NOT NULL,
    updatedAt TIMESTAMP NOT NULL,
    FOREIGN KEY (productId) REFERENCES product(productId),
    FOREIGN KEY (userId) REFERENCES "user"(userId)
);

CREATE TABLE wishlist (
    wishlistId BIGINT PRIMARY KEY,
    userId BIGINT NOT NULL,
    productId BIGINT NOT NULL,
    FOREIGN KEY (userId) REFERENCES "user"(userId),
    FOREIGN KEY (productId) REFERENCES product(productId)
);

CREATE TABLE cart (
    cartId BIGINT PRIMARY KEY,
    userId BIGINT NOT NULL,
    productId BIGINT NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (userId) REFERENCES "user"(userId),
    FOREIGN KEY (productId) REFERENCES product(productId)
);

CREATE TABLE orderStatus (
    orderStatusId INT PRIMARY KEY,
    orderStatusName VARCHAR(100) NOT NULL
);

CREATE TABLE "order" (
    orderId BIGINT PRIMARY KEY,
    userId BIGINT NOT NULL,
    orderStatusId INT NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    addressId BIGINT NOT NULL,
    deliveryType VARCHAR(20) NOT NULL,
    paymentType VARCHAR(20) NOT NULL,
    paymentStatus VARCHAR(20) NOT NULL,
    note VARCHAR(100),
    createdAt TIMESTAMP NOT NULL,
    FOREIGN KEY (userId) REFERENCES "user"(userId),
    FOREIGN KEY (orderStatusId) REFERENCES orderStatus(orderStatusId),
    FOREIGN KEY (addressId) REFERENCES address(addressId)
);

CREATE TABLE orderItem (
    orderItemId BIGINT PRIMARY KEY,
    orderId BIGINT NOT NULL,
    productId BIGINT NOT NULL,
    quantity INT NOT NULL,
    unitPrice DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (orderId) REFERENCES "order"(orderId),
    FOREIGN KEY (productId) REFERENCES product(productId)
);

CREATE TABLE parentChild (
    parentChildId BIGINT PRIMARY KEY,
    userId BIGINT NOT NULL,
    childId BIGINT NOT NULL,
    FOREIGN KEY (userId) REFERENCES "user"(userId),
    FOREIGN KEY (childId) REFERENCES "user"(userId)
);

CREATE TABLE auditLog (
    auditLogId BIGINT PRIMARY KEY,
    userId BIGINT NOT NULL,
    action VARCHAR(100) NOT NULL,
    tableName VARCHAR(100) NOT NULL,
    recordId BIGINT NOT NULL,
    oldValues JSON,
    newValues JSON,
    createdAt TIMESTAMP NOT NULL,
    FOREIGN KEY (userId) REFERENCES "user"(userId)
);

