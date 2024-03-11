/*
 Navicat Premium Data Transfer

 Source Server         : root
 Source Server Type    : MySQL
 Source Server Version : 80036
 Source Host           : localhost:3306
 Source Schema         : biosecurity_guide

 Target Server Type    : MySQL
 Target Server Version : 80036
 File Encoding         : 65001

 Date: 10/03/2024 06:44:03
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for staff_admin
-- ----------------------------
DROP TABLE IF EXISTS `staff_admin`;
CREATE TABLE `staff_admin`  (
  `ID` int NOT NULL AUTO_INCREMENT,
  `First_Name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Last_Name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Work_Phone_number` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Hire_date` datetime NULL DEFAULT NULL,
  `Position` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Department` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `Status` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `SecureAccountID` int NULL DEFAULT NULL,
  PRIMARY KEY (`ID`) USING BTREE,
  INDEX `fk_secureaccount_id1`(`SecureAccountID`) USING BTREE,
  CONSTRAINT `fk_secureaccount_id1` FOREIGN KEY (`SecureAccountID`) REFERENCES `secureaccount` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of staff_admin
-- ----------------------------
INSERT INTO `staff_admin` VALUES (1, 'Alice12', 'Johnson12', 'alice.johnson@gmail.com', '90874932212', '2023-01-11 00:00:00', 'Staff', 'Developer12', 'Active', 8);
INSERT INTO `staff_admin` VALUES (2, 'Bob', 'Smith', 'bob.smith@gmail.com', '123456789', '2023-02-15 00:00:00', 'Administration', 'Project Management', 'Active', 9);
INSERT INTO `staff_admin` VALUES (3, 'Charlie', 'Davis', 'charlie.davis@gmail.com', '389074932', '2022-11-01 00:00:00', 'Staff', 'Design', 'Inactive', 10);
INSERT INTO `staff_admin` VALUES (4, 'Diana', 'Martinez', 'diana.martinez@gmail.com', '987602937', '2021-03-05 00:00:00', 'Staff', 'Data Analysis', 'Active', 11);

SET FOREIGN_KEY_CHECKS = 1;
