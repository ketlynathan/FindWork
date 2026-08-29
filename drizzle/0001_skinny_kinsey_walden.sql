CREATE TABLE `agentActivities` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`profileId` int,
	`agent` enum('analyst','recruiter','career_editor','integration_guard') NOT NULL,
	`title` varchar(240) NOT NULL,
	`detail` text NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `agentActivities_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `applications` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`profileId` int NOT NULL,
	`jobId` int NOT NULL,
	`status` enum('draft','approved','submitted','rejected','archived') NOT NULL DEFAULT 'draft',
	`adaptedResume` text NOT NULL,
	`adaptationNote` text NOT NULL,
	`approvalConfirmed` boolean NOT NULL DEFAULT false,
	`approvedAt` timestamp,
	`submittedAt` timestamp,
	`applicationUrl` varchar(2048) NOT NULL,
	`activityLog` json NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `applications_id` PRIMARY KEY(`id`),
	CONSTRAINT `application_profile_job_idx` UNIQUE(`userId`,`profileId`,`jobId`)
);
--> statement-breakpoint
CREATE TABLE `candidateProfiles` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`label` varchar(120) NOT NULL,
	`professionalArea` varchar(160) NOT NULL,
	`targetRole` varchar(180) NOT NULL,
	`seniority` varchar(80) NOT NULL,
	`summary` text NOT NULL,
	`skills` json NOT NULL,
	`regions` json NOT NULL,
	`workModes` json NOT NULL,
	`resumeText` text NOT NULL,
	`isPrimary` boolean NOT NULL DEFAULT false,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `candidateProfiles_id` PRIMARY KEY(`id`),
	CONSTRAINT `candidate_profile_owner_label_idx` UNIQUE(`userId`,`label`)
);
--> statement-breakpoint
CREATE TABLE `integrations` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`provider` varchar(120) NOT NULL,
	`accountLabel` varchar(180) NOT NULL,
	`connectionMethod` enum('official_oauth','authorized_api','assisted_link') NOT NULL,
	`status` enum('not_connected','pending','connected','attention_required') NOT NULL DEFAULT 'not_connected',
	`capabilities` json NOT NULL,
	`secretReference` varchar(180),
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `integrations_id` PRIMARY KEY(`id`),
	CONSTRAINT `integration_owner_provider_account_idx` UNIQUE(`userId`,`provider`,`accountLabel`)
);
--> statement-breakpoint
CREATE TABLE `jobAnalyses` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`profileId` int NOT NULL,
	`jobId` int NOT NULL,
	`matchScore` int NOT NULL,
	`priority` enum('high','medium','low') NOT NULL,
	`shouldApply` boolean NOT NULL,
	`breakdown` json NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `jobAnalyses_id` PRIMARY KEY(`id`),
	CONSTRAINT `job_analysis_profile_job_idx` UNIQUE(`userId`,`profileId`,`jobId`)
);
--> statement-breakpoint
CREATE TABLE `jobs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`title` varchar(220) NOT NULL,
	`company` varchar(220) NOT NULL,
	`location` varchar(220) NOT NULL,
	`region` varchar(160) NOT NULL,
	`professionalArea` varchar(160) NOT NULL,
	`workMode` enum('remote','hybrid','onsite','flexible') NOT NULL,
	`source` varchar(120) NOT NULL,
	`sourceUrl` varchar(2048) NOT NULL,
	`description` text NOT NULL,
	`structuredRequirements` json,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `jobs_id` PRIMARY KEY(`id`),
	CONSTRAINT `job_owner_url_idx` UNIQUE(`userId`,`sourceUrl`)
);
--> statement-breakpoint
ALTER TABLE `agentActivities` ADD CONSTRAINT `agentActivities_userId_users_id_fk` FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `agentActivities` ADD CONSTRAINT `agentActivities_profileId_candidateProfiles_id_fk` FOREIGN KEY (`profileId`) REFERENCES `candidateProfiles`(`id`) ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `applications` ADD CONSTRAINT `applications_userId_users_id_fk` FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `applications` ADD CONSTRAINT `applications_profileId_candidateProfiles_id_fk` FOREIGN KEY (`profileId`) REFERENCES `candidateProfiles`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `applications` ADD CONSTRAINT `applications_jobId_jobs_id_fk` FOREIGN KEY (`jobId`) REFERENCES `jobs`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `candidateProfiles` ADD CONSTRAINT `candidateProfiles_userId_users_id_fk` FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `integrations` ADD CONSTRAINT `integrations_userId_users_id_fk` FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `jobAnalyses` ADD CONSTRAINT `jobAnalyses_userId_users_id_fk` FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `jobAnalyses` ADD CONSTRAINT `jobAnalyses_profileId_candidateProfiles_id_fk` FOREIGN KEY (`profileId`) REFERENCES `candidateProfiles`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `jobAnalyses` ADD CONSTRAINT `jobAnalyses_jobId_jobs_id_fk` FOREIGN KEY (`jobId`) REFERENCES `jobs`(`id`) ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE `jobs` ADD CONSTRAINT `jobs_userId_users_id_fk` FOREIGN KEY (`userId`) REFERENCES `users`(`id`) ON DELETE cascade ON UPDATE no action;