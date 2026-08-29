CREATE TABLE `resumeDocuments` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`profileId` int NOT NULL,
	`fileName` varchar(255) NOT NULL,
	`mimeType` varchar(120) NOT NULL,
	`storageKey` varchar(512) NOT NULL,
	`storageUrl` varchar(1024) NOT NULL,
	`sizeBytes` int NOT NULL,
	`isActive` boolean NOT NULL DEFAULT true,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `resumeDocuments_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
ALTER TABLE `resumeDocuments` ADD CONSTRAINT `resumeDocuments_userId_users_id_fk` FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `resumeDocuments` ADD CONSTRAINT `resumeDocuments_profileId_candidateProfiles_id_fk` FOREIGN KEY (`profileId`) REFERENCES `candidateProfiles`(`id`) ON DELETE cascade ON UPDATE no action;