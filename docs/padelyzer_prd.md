Updated Padelyzer - Documento de Requisitos del Producto
Overview
Padelyzer is a comprehensive AI-powered padel analysis platform that processes videos, delivers detailed performance metrics, and enhances player, coach, and club experiences through data-driven insights. The platform targets amateur and professional players, coaches, and padel clubs, offering video analysis, social features, gamification, and club management tools. By May 31, 2025, Padelyzer aims to support 1.3M users with a 2.5% churn rate, generating revenue through subscriptions (Social: $79 MXN, Premium: $199 MXN, Coaches: $274 MXN, Elite: $299 MXN), microtransactions, and advertising.

Core Features
1. Video Analysis
Funcionality: Process 720p videos (MP4, AVI, MOV) to detect players, strokes (derecha, revés, saque, etc.), and metrics (posture, reaction time, speed, court coverage) using Google Cloud Video Intelligence and MediaPipe.
Importance: Enables Padel IQ calculation and personalized feedback, critical for player improvement and engagement.
Implementation:
Validate video resolution (720p minimum).
Support training (single player) and match (multiple players) videos with interactive court position selection.
Generate preview with bounding boxes and pose detection.
Tasks:
Optimize video processing with chunked uploads (video_optimize).
Support multiple formats (video_formats).
Refine stroke detection with MediaPipe/Google Cloud (analysis_strokes).
Store video versions for history (storage_versioning).
2. Padel IQ System
Functionality: Calculate Padel IQ based on video analysis, tracking metrics (technique, rhythm, strength, coverage) and providing comparative metrics for gamification.
Importance: Quantifies player performance, drives retention (2.5% churn), and supports matchmaking.
Implementation:
Update Padel IQ after each analysis.
Compare players for gamification (e.g., vs. friends).
Store metrics in Firestore (video_analyses, padel_iq_history).
Tasks:
Update Padel IQ metrics (padel_iq_metrics).
Implement player comparison (padel_iq_comparison).
3. Social and Gamification Features
Functionality: Enable friend connections, social wall posts, chat, gamification (points, badges, challenges), and event management (6 events/month).
Importance: Supports 0.7 referidos/user/month, reduces churn via community engagement, and drives organic growth.
Implementation:
Manage friendships (requests, accept/reject).
Post and comment on social wall.
Track gamification data (e.g., “Sube 5 derechas” challenge).
Create and manage events for user acquisition (150 users/month via events).
Tasks:
Implement friend request CRUD (endpoints_friend_requests).
Implement social wall CRUD (endpoints_posts).
Enhance gamification endpoints (endpoints_gamification).
Implement event endpoints (endpoints_events).
Implement referral endpoints (endpoints_referrals).
4. Matchmaking and Tournaments
Functionality: Pair players for matches, manage tournaments and leagues, and track real-time match stats and rankings.
Importance: Enhances user engagement and supports club module integration.
Implementation:
Use Distance Matrix and Places APIs for location-based matchmaking.
Manage match creation, updates, and cancellations.
Track tournament/league participation and rankings.
Tasks:
Implement matchmaking endpoint (endpoints_matchmaking).
Implement match CRUD (endpoints_matches).
Implement tournament and league endpoints (endpoints_tournaments, endpoints_leagues).
Implement rankings and match stats (endpoints_rankings, endpoints_match_stats).
Enable real-time match updates (partidos_realtime).
Process historical match data (estadisticas_historical).
5. User Management and Subscriptions
Functionality: Register users, manage profiles, roles (user, admin, Padel Ambassador), and subscriptions (Social, Premium, Coaches, Elite).
Importance: Supports 1.3M users, revenue generation, and Padel Ambassador program (130 Ambassadors by month 18).
Implementation:
Handle user registration, profile updates, and deactivation.
Manage subscriptions via Stripe.
Assign roles for access control (e.g., admin for /admin/*).
Tasks:
Implement user CRUD (endpoints_register_user, endpoints_users).
Implement profile management (users_profile).
Implement role system (auth_roles).
Implement subscription endpoints (endpoints_subscriptions).
Implement password recovery (auth_recovery).
6. Notifications and Communication
Functionality: Send push notifications, emails, and in-app alerts for events, referidos, match invites, and Padel Ambassador tasks.
Importance: Drives engagement, supports retention, and ensures timely communication.
Implementation:
Schedule notifications for events and referidos.
Use templates for friend requests, match invites, and posts.
Send custom emails for subscriptions and events.
Tasks:
Implement scheduled notifications (notifications_scheduled).
Implement push notification templates (notifications_templates).
Create custom email templates (email_templates).
Implement notification endpoint (endpoints_notifications).
Implement chat endpoint (endpoints_chat).
7. Dashboard and Analytics
Functionality: Display user progress (Padel IQ, stroke completion), gamification metrics, match stats, and operational insights for admins.
Importance: Enhances user experience and supports admin module functionality.
Implementation:
Visualize progress (e.g., “Progreso del Padel IQ: X%”).
Show gamification data (ranks, badges).
Provide admin dashboards for financial and operational metrics.
Tasks:
Implement dashboard data via /api/get_profile, /api/gamification, /api/match_stats.
Process historical data for analytics (estadisticas_historical).
8. Club and League Management
Functionality: Manage clubs, leagues, and tournaments independently, with integration to Padelyzer (e.g., import Padel IQ).
Importance: Supports club partnerships and user acquisition.
Implementation:
Create/edit/delete leagues and tournaments.
Register players via QR/enlace.
Integrate with Padelyzer via /api/padel_iq, /api/match/update.
Tasks:
Implement tournament and league endpoints (endpoints_tournaments, endpoints_leagues).
Implement match updates (endpoints_matches).
9. Onboarding
Functionality: Guide users through initial setup (video upload, profile completion).
Importance: Improves conversion (48% in month 2, 65% in month 18).
Implementation:
Track onboarding steps in Firestore.
Provide interactive tutorials.
Tasks:
Implement onboarding endpoint (endpoints_onboarding).
User Experience
User Personas
Jugador Amateur
Needs: Basic video analysis, matchmaking, social connections.
Goals: Improve specific strokes, find players, engage in community.
Interface: Simple dashboard, gamification badges, event notifications.
Entrenador Profesional
Needs: Detailed metrics, player comparisons, exportable reports.
Goals: Analyze student progress, tailor coaching plans.
Interface: Advanced analytics, historical data, admin access.
Club de Pádel
Needs: League/tournament management, player registration, Padel IQ integration.
Goals: Streamline operations, attract players.
Interface: Club admin dashboard, QR-based registration.
Padel Ambassador
Needs: Event creation tools, task notifications, free Elite plan.
Goals: Organize events, reduce churn, invite users.
Interface: Ambassador dashboard, notification alerts.
Key User Flows
Video Upload and Analysis:
Upload video → Validate resolution → Select video type → Choose position → Review preview → View Padel IQ and metrics.
Matchmaking:
Search players by location/Padel IQ → Propose match → Receive notification → Confirm match.
Social Engagement:
Add friend via QR → Post to social wall → Comment/like → Receive notifications.
Subscription and Referrals:
Start 14-day trial → Convert to paid plan → Invite friends → Earn trial extensions.
Event Participation:
View events → Register → Receive reminders → Attend and connect.
Club Management:
Create league → Register players → Schedule matches → View rankings.
Technical Architecture
System Components
Backend Services (Microservices with RabbitMQ for async tasks):
Authentication: User login, role management, password recovery (auth_service.py, auth_roles, auth_recovery).
Video: Video upload, processing, format validation (video_service.py, video_optimize, video_formats).
Analysis: Stroke detection, metric calculation (analysis_manager.py, analysis_strokes).
Notifications: Push, email, and in-app alerts (notifications.py, notifications_scheduled, notifications_templates).
Email: Custom email delivery (email.py, email_templates).
Storage: Video and file management (storage_service.py, storage_versioning).
PadelIQ: Padel IQ calculation, comparisons (padel_iq_service.py, padel_iq_metrics, padel_iq_comparison).
Firebase: Real-time database, auth integration (firebase.py, firebase_queries).
Users: Profile and role management (users_profile, auth_roles).
Partidos: Real-time match management (partidos_realtime).
Estadísticas: Historical data and rankings (estadisticas_historical).
Frontend:
React Native app for players (Expo integration, expo_endpoints, websocket, cache_system).
Web admin dashboard for clubs/admins (React, expo_docs).
Interactive visualizations (charts, progress bars).
Infrastructure:
Docker containers for microservices.
Firebase Firestore for data (db_indexes, db_migrations, db_backups, db_cache).
Firebase Storage for videos.
AWS for deployment (ci_cd, staging_env, prod_monitoring).
CloudWatch for logging (logging).
Data Models (Firestore Collections)
users: user_id, email, name, padel_iq, role, subscription_status, location, stats (matches_played, achievements).
friend_requests: request_id, sender_id, receiver_id, status.
friends: friendship_id, user_id_1, user_id_2.
matches: match_id, creator_id, participants, status, location, ratings.
posts: post_id, user_id, content, media_url, likes.
video_analyses: analysis_id, user_id, video_url, tipo_video, metrics (padel_iq, tecnica).
subscriptions: subscription_id, user_id, plan_id, status.
notifications: notification_id, user_id, type, message, read.
Additional Collections (from app definition):
padel_iq_history: player_id, timestamp, padel_iq, confidence.
match_proposals: proposer_id, receiver_id, club, time, status.
clubs: name, location, place_id.
Tasks:
Apply migrations for schema updates (db_migrations).
Optimize indexes for queries (db_indexes).
Set up backups (db_backups).
Cache frequent queries (db_cache).
API Endpoints (17 + CRUD)
Core Endpoints (from API documentation):
/api/register_user (POST): Create user.
/api/get_profile (GET): Read profile.
/api/calculate_padel_iq (POST): Update Padel IQ.
/api/sessions (GET): Read sessions.
/api/subscriptions (GET): Read subscriptions.
/api/friends (GET): Read friends.
/api/notifications (GET): Read notifications.
/api/social_wall (GET): Read posts.
/api/chat (GET): Read conversations.
/api/gamification (GET): Read gamification data.
/api/calendar (GET): Read events.
/api/tournaments (GET): Read tournaments.
/api/leagues (GET): Read leagues.
/api/rankings (GET): Read rankings.
/api/match_stats (GET): Read match stats.
/api/matchmaking (GET/POST): Create/read matches.
/api/onboarding (POST): Create/update onboarding.
CRUD Endpoints:
/api/users/{user_id} (PUT/DELETE): Update/delete user.
/api/friend_requests (POST): Create friend request.
/api/friend_requests/{request_id} (PUT): Update request.
/api/matches (POST): Create match.
/api/matches/{match_id} (PUT/DELETE): Update/delete match.
/api/posts (POST): Create post.
/api/posts/{post_id} (PUT/DELETE): Update/delete post.
/api/events (POST/PUT/DELETE): Create/update/delete event.
/api/referrals (POST/GET): Create/read referral.
Tasks:
Implement all endpoints (endpoints_*).
Validate inputs with Zod (zod_validation).
Secure with JWT (jwt_auth) and Firestore rules (firestore_rules).
Development Roadmap
Fase 1: MVP (Sessions 1–8, April 29–May 14, 2025)
Goals: Launch core app with basic analysis, user management, and social features.
Tasks:
Configuration/Security: Env variables (config_env), JWT (jwt_auth), CORS (cors_setup), rate limiting (rate_limit), Zod validation (zod_validation), Firestore rules (firestore_rules), RabbitMQ (rabbitmq_setup), logging (logging).
Database: Indexes (db_indexes), migrations (db_migrations), backups (db_backups), caching (db_cache).
Endpoints/CRUD: User CRUD (endpoints_register_user, endpoints_users), friend requests (endpoints_friend_requests), matches (endpoints_matches), posts (endpoints_posts), events (endpoints_events), referrals (endpoints_referrals), matchmaking (endpoints_matchmaking), onboarding (endpoints_onboarding).
Microservices: Password recovery (auth_recovery), role system (auth_roles), profile management (users_profile), email templates (email_templates).
Fase 2: Core Enhancements (Sessions 9–12, May 15–May 22, 2025)
Goals: Enhance analysis, notifications, and real-time features.
Tasks:
Endpoints/CRUD: Padel IQ (endpoints_calculate_padel_iq), sessions (endpoints_sessions), subscriptions (endpoints_subscriptions), friends (endpoints_friends), notifications (endpoints_notifications), social wall (endpoints_social_wall), chat (endpoints_chat), gamification (endpoints_gamification), calendar (endpoints_calendar), tournaments (endpoints_tournaments), leagues (endpoints_leagues), rankings (endpoints_rankings), match stats (endpoints_match_stats).
Microservices: Video processing (video_optimize), stroke detection (analysis_strokes), Padel IQ metrics (padel_iq_metrics), player comparison (padel_iq_comparison), scheduled notifications (notifications_scheduled), push templates (notifications_templates), real-time matches (partidos_realtime), historical stats (estadisticas_historical), query optimization (firebase_queries).
Fase 3: Testing and Deployment (Sessions 13–16, May 23–May 31, 2025)
Goals: Ensure stability, scalability, and production readiness.
Tasks:
Integration: Expo endpoints (expo_endpoints), WebSocket (websocket), cache system (cache_system), Expo docs (expo_docs).
Testing/Documentation: Unit tests (unit_tests), integration tests (integration_tests), Swagger docs (swagger_docs), install guide (install_guide).
Deployment: CI/CD (ci_cd), staging environment (staging_env), production monitoring (prod_monitoring), deploy guide (deploy_guide).
Fase 4: Post-Launch (June 2025+)
Goals: Add advanced features and optimizations.
Tasks (Deferred):
Two-factor authentication (auth_2fa).
Video compression (video_compression).
Additional format support (video_formats).
Real-time analysis (analysis_realtime).
Notification priority system (notifications_priority).
Storage permission enhancements (storage_permissions).
Logical Dependency Chain
Foundation (Sessions 1–5):
Configuration: Env variables, JWT, CORS, rate limiting, Zod, Firestore rules, RabbitMQ, logging.
Database: Indexes, migrations, backups, caching.
Microservices: Role system, profile management, email templates.
Core Functionality (Sessions 6–9):
Endpoints: User CRUD, friend requests, matches, posts, events, referrals, matchmaking, onboarding, Padel IQ, subscriptions, friends, notifications, social wall, chat, gamification, calendar, tournaments, leagues, rankings, match stats.
Microservices: Password recovery, video processing, stroke detection, Padel IQ metrics, player comparison.
Enhancements and Integration (Sessions 10–12):
Microservices: Scheduled notifications, push templates, real-time matches, historical stats, query optimization.
Integration: Expo endpoints, WebSocket, cache system.
Testing and Deployment (Sessions 13–16):
Testing: Unit and integration tests, Swagger docs.
Deployment: CI/CD, staging, monitoring, deploy guide.
Risks and Mitigations
Technical Challenges
Video Processing:
Risk: High resource consumption for 1.3M users.
Mitigation: Chunked uploads (video_optimize), RabbitMQ for async processing (rabbitmq_setup).
Analysis Precision:
Risk: Inaccurate stroke detection.
Mitigation: Refine MediaPipe/Google Cloud models (analysis_strokes), continuous ML improvement.
Scalability:
Risk: Database and API overload.
Mitigation: Firestore indexes (db_indexes), query caching (db_cache), rate limiting (rate_limit).
Security:
Risk: Unauthorized access to admin endpoints.
Mitigation: JWT (jwt_auth), Firestore rules (firestore_rules), role system (auth_roles).
Real-Time Performance:
Risk: Latency in match updates.
Mitigation: WebSocket (websocket), Firebase real-time (firebase_queries).
Business Risks
User Acquisition:
Risk: Missing 1.3M user target.
Mitigation: Referral endpoints (endpoints_referrals), event management (endpoints_events), Padel Ambassadors (notifications_scheduled).
Churn:
Risk: Exceeding 2.5% churn.
Mitigation: Gamification (endpoints_gamification), social features (endpoints_social_wall), notifications (notifications_templates).
Appendix
Technical Specifications
Backend: Python 3.9+, FastAPI, YOLOv8 (instead of Google Cloud Video Intelligence for real-time), MediaPipe.
Frontend: React Native (Expo), React (admin dashboard).
Database: Firebase Firestore, Firebase Storage.
Infrastructure: Docker, AWS, RabbitMQ, CloudWatch.
Security: JWT, Zod, Firebase Authentication.
APIs: Google Maps, Places, Distance Matrix, Stripe.