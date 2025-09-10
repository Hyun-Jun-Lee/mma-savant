# MMA Savant 시스템 DSL 설계 (FastAPI + PostgreSQL + Redis 통합)

## 1. 시스템 아키텍처

```dsl
system Architecture {
    backend: FastAPI
    database: PostgreSQL + Redis
    frontend: None (API Only)
    structure: Modular Monolithic
    
    modules: [
        User,
        Authentication, 
        Fighter,
        Match,
        Event,
        Conversation,
        DataCollector,
        LLM,
        Composition,
        WebAPI
    ]
}
```

## 2. 데이터베이스 스키마

```dsl
database Schema {
    
    table users {
        id: INTEGER PRIMARY KEY
        username: TEXT UNIQUE
        email: TEXT UNIQUE
        profile_image_url: TEXT
        is_active: BOOLEAN DEFAULT true
        created_at: DATETIME
        updated_at: DATETIME
    }
    
    table conversations {
        id: INTEGER PRIMARY KEY
        user_id: INTEGER FOREIGN KEY -> users(id)
        session_id: TEXT UNIQUE
        title: TEXT
        messages: JSON  // 전체 대화 메시지 배열
        created_at: DATETIME
        updated_at: DATETIME
    }
    
    table fighters {
        id: INTEGER PRIMARY KEY
        name: TEXT NOT NULL
        nickname: TEXT
        height: FLOAT
        height_cm: FLOAT
        weight: FLOAT
        weight_kg: FLOAT
        reach: FLOAT
        reach_cm: FLOAT
        stance: TEXT
        birthdate: TEXT
        belt: BOOLEAN DEFAULT false
        detail_url: TEXT
        wins: INTEGER DEFAULT 0
        losses: INTEGER DEFAULT 0
        draws: INTEGER DEFAULT 0
        created_at: DATETIME
        updated_at: DATETIME
    }
    
    table rankings {
        id: INTEGER PRIMARY KEY
        fighter_id: INTEGER FOREIGN KEY -> fighters(id)
        ranking: INTEGER
        weight_class_id: INTEGER
        created_at: DATETIME
        updated_at: DATETIME
    }
    
    table events {
        id: INTEGER PRIMARY KEY
        name: TEXT NOT NULL
        date: DATE
        location: TEXT
        venue: TEXT
        detail_url: TEXT
        created_at: DATETIME
        updated_at: DATETIME
    }
    
    table matches {
        id: INTEGER PRIMARY KEY
        event_id: INTEGER FOREIGN KEY -> events(id)
        title: TEXT
        weight_class: TEXT
        bonus: TEXT
        created_at: DATETIME
        updated_at: DATETIME
    }
    
    table fighter_matches {
        id: INTEGER PRIMARY KEY
        match_id: INTEGER FOREIGN KEY -> matches(id)
        fighter_id: INTEGER FOREIGN KEY -> fighters(id)
        result: TEXT  // WIN | LOSS | DRAW | NC
        method: TEXT
        round: INTEGER
        time: TEXT
        created_at: DATETIME
        updated_at: DATETIME
    }
    
    table sig_str_match_stats {
        id: INTEGER PRIMARY KEY
        fighter_match_id: INTEGER FOREIGN KEY -> fighter_matches(id)
        sig_str_landed: INTEGER
        sig_str_attempted: INTEGER
        sig_str_pct: FLOAT
        total_str_landed: INTEGER
        total_str_attempted: INTEGER
        td_landed: INTEGER
        td_attempted: INTEGER
        td_pct: FLOAT
        sub_att: INTEGER
        rev: INTEGER
        ctrl: TEXT
        created_at: DATETIME
        updated_at: DATETIME
    }
    
    table basic_match_stats {
        id: INTEGER PRIMARY KEY
        fighter_match_id: INTEGER FOREIGN KEY -> fighter_matches(id)
        kd: INTEGER  // Knockdowns
        sig_str: TEXT
        sig_str_pct: TEXT
        total_str: TEXT
        td: TEXT
        td_pct: TEXT
        sub_att: INTEGER
        rev: INTEGER
        ctrl: TEXT
        created_at: DATETIME
        updated_at: DATETIME
    }
}
```

## 3. 모듈별 정의

```dsl
module User {
    
    // Repository Layer (PostgreSQL 연동)
    repository UserRepository {
        function save(user: UserModel) -> Result<int, Error>
        function findById(id: int) -> Result<UserModel, Error>
        function findByEmail(email: String) -> Result<UserModel, Error>
        function findByUsername(username: String) -> Result<UserModel, Error>
        function findAll() -> List<UserModel>
        function deleteById(id: int) -> Result<Void, Error>
        function updateUser(id: int, user: UserModel) -> Result<UserModel, Error>
    }
    
    // Service Layer
    service UserService {
        function createUser(user: UserSchema) -> Result<UserModel, Error>
        function getUser(id: int) -> Result<UserModel, Error>
        function getUserByEmail(email: String) -> Result<UserModel, Error>
        function updateUser(id: int, user: UserSchema) -> Result<UserModel, Error>
        function deleteUser(id: int) -> Result<Void, Error>
        function getAllUsers() -> List<UserModel>
    }
    
    // API Router
    router UserRouter {
        POST   /api/users           -> createUser
        GET    /api/users/{id}      -> getUser
        PUT    /api/users/{id}      -> updateUser
        DELETE /api/users/{id}      -> deleteUser
        GET    /api/users           -> getAllUsers
    }
    
    // Types
    type UserModel {
        id: int
        username: String
        email: String
        profileImageUrl: String?
        isActive: Boolean
        createdAt: DateTime
        updatedAt: DateTime
    }
    
    type UserSchema {
        username: String
        email: String
        profileImageUrl: String?
        isActive: Boolean?
    }
}

module Authentication {
    
    // JWT Handler
    service JWTHandler {
        function decodeToken(token: String) -> Result<TokenData, Error>
        function createAccessToken(data: Dict<String, Any>) -> String
        function verifyTokenExpiry(tokenData: TokenData) -> Boolean
    }
    
    // API Router
    router AuthRouter {
        POST   /api/auth/login      -> authenticateUser
        POST   /api/auth/logout     -> logoutUser
        POST   /api/auth/refresh    -> refreshToken
        GET    /api/auth/me         -> getCurrentUser
    }
    
    // Dependencies
    dependency Dependencies {
        function getCurrentUser(token: String) -> Result<UserModel, Error>
        function verifyToken(token: String) -> Result<TokenData, Error>
    }
    
    // Types
    type TokenData {
        sub: String  // user id or email
        email: String?
        name: String?
        picture: String?
        iat: int?
        exp: int?
    }
}

module Fighter {
    
    // Repository Layer
    repository FighterRepository {
        function save(fighter: FighterModel) -> Result<int, Error>
        function findById(id: int) -> Result<FighterModel, Error>
        function findByName(name: String) -> List<FighterModel>
        function findAll() -> List<FighterModel>
        function deleteById(id: int) -> Result<Void, Error>
        function updateFighter(id: int, fighter: FighterModel) -> Result<FighterModel, Error>
        function searchFighters(query: String) -> List<FighterModel>
    }
    
    // Service Layer
    service FighterService {
        function createFighter(fighter: FighterSchema) -> Result<FighterModel, Error>
        function getFighter(id: int) -> Result<FighterModel, Error>
        function searchFighters(query: String) -> List<FighterModel>
        function updateFighter(id: int, fighter: FighterSchema) -> Result<FighterModel, Error>
        function deleteFighter(id: int) -> Result<Void, Error>
        function getFighterStats(id: int) -> Result<FighterStats, Error>
    }
    
    // API Router (외부 노출 없음 - 내부 서비스용)
    service FighterAPI {
        // 향후 필요시 REST API 추가 예정
    }
    
    // Types
    type FighterModel {
        id: int
        name: String
        nickname: String?
        height: Float?
        heightCm: Float?
        weight: Float?
        weightKg: Float?
        reach: Float?
        reachCm: Float?
        stance: String?
        birthdate: String?
        belt: Boolean
        detailUrl: String?
        wins: int
        losses: int
        draws: int
        createdAt: DateTime
        updatedAt: DateTime
        fighterMatches: List<FighterMatchModel>
        rankings: List<RankingModel>
    }
    
    type FighterSchema {
        name: String
        nickname: String?
        height: Float?
        heightCm: Float?
        weight: Float?
        weightKg: Float?
        reach: Float?
        reachCm: Float?
        stance: String?
        belt: Boolean?
        birthdate: Date?
        detailUrl: String?
        wins: int?
        losses: int?
        draws: int?
    }
    
    type RankingModel {
        id: int
        fighterId: int
        ranking: int?
        weightClassId: int?
        createdAt: DateTime
        updatedAt: DateTime
    }
}

module Match {
    
    // Repository Layer
    repository MatchRepository {
        function save(match: MatchModel) -> Result<int, Error>
        function findById(id: int) -> Result<MatchModel, Error>
        function findByEventId(eventId: int) -> List<MatchModel>
        function findAll() -> List<MatchModel>
        function deleteById(id: int) -> Result<Void, Error>
        function saveFighterMatch(fighterMatch: FighterMatchModel) -> Result<int, Error>
        function saveMatchStats(stats: SigStrMatchStatModel) -> Result<int, Error>
    }
    
    // Service Layer
    service MatchService {
        function createMatch(match: MatchSchema) -> Result<MatchModel, Error>
        function getMatch(id: int) -> Result<MatchModel, Error>
        function getMatchesByEvent(eventId: int) -> List<MatchModel>
        function addFighterToMatch(matchId: int, fighterMatch: FighterMatchSchema) -> Result<FighterMatchModel, Error>
        function getMatchResults(matchId: int) -> Result<MatchResults, Error>
        function getDetailedMatchStats(matchId: int) -> Result<DetailedMatchStats, Error>
    }
    
    // Types
    type MatchModel {
        id: int
        eventId: int
        title: String?
        weightClass: String?
        bonus: String?
        createdAt: DateTime
        updatedAt: DateTime
        event: EventModel
        fighterMatches: List<FighterMatchModel>
    }
    
    type FighterMatchModel {
        id: int
        matchId: int
        fighterId: int
        result: String?  // WIN | LOSS | DRAW | NC
        method: String?
        round: int?
        time: String?
        createdAt: DateTime
        updatedAt: DateTime
        fighter: FighterModel
        match: MatchModel
        sigStrStats: SigStrMatchStatModel?
        basicStats: BasicMatchStatModel?
    }
    
    type SigStrMatchStatModel {
        id: int
        fighterMatchId: int
        sigStrLanded: int?
        sigStrAttempted: int?
        sigStrPct: Float?
        totalStrLanded: int?
        totalStrAttempted: int?
        tdLanded: int?
        tdAttempted: int?
        tdPct: Float?
        subAtt: int?
        rev: int?
        ctrl: String?
        createdAt: DateTime
        updatedAt: DateTime
    }
}

module Event {
    
    // Repository Layer
    repository EventRepository {
        function save(event: EventModel) -> Result<int, Error>
        function findById(id: int) -> Result<EventModel, Error>
        function findByDate(date: Date) -> List<EventModel>
        function findAll() -> List<EventModel>
        function deleteById(id: int) -> Result<Void, Error>
        function findByLocation(location: String) -> List<EventModel>
    }
    
    // Service Layer
    service EventService {
        function createEvent(event: EventSchema) -> Result<EventModel, Error>
        function getEvent(id: int) -> Result<EventModel, Error>
        function getEventsByDate(date: Date) -> List<EventModel>
        function getUpcomingEvents() -> List<EventModel>
        function getPastEvents() -> List<EventModel>
        function getEventWithMatches(id: int) -> Result<EventWithMatches, Error>
    }
    
    // Types
    type EventModel {
        id: int
        name: String
        date: Date?
        location: String?
        venue: String?
        detailUrl: String?
        createdAt: DateTime
        updatedAt: DateTime
        matches: List<MatchModel>
    }
    
    type EventSchema {
        name: String
        date: Date?
        location: String?
        venue: String?
        detailUrl: String?
    }
}

module Conversation {
    
    // Repository Layer
    repository ConversationRepository {
        function save(conversation: ConversationModel) -> Result<int, Error>
        function findById(id: int) -> Result<ConversationModel, Error>
        function findBySessionId(sessionId: String) -> Result<ConversationModel, Error>
        function findByUserId(userId: int) -> List<ConversationModel>
        function findByUserIdPaginated(userId: int, limit: int, offset: int) -> List<ConversationModel>
        function deleteById(id: int) -> Result<Void, Error>
        function updateMessages(id: int, messages: List<ChatMessage>) -> Result<ConversationModel, Error>
    }
    
    // Service Layer
    service ChatSessionService {
        function createNewSession(db: AsyncSession, userId: int, sessionData: ChatSessionCreate) -> Result<ChatSessionResponse, Error>
        function getUserSessions(db: AsyncSession, userId: int, limit: int, offset: int) -> Result<ChatSessionListResponse, Error>
        function getSessionById(db: AsyncSession, sessionId: String, userId: int) -> Result<ChatSessionResponse, Error>
        function addMessageToSession(db: AsyncSession, sessionId: String, message: ChatMessageCreate, userId: int) -> Result<ChatMessageResponse, Error>
        function updateSessionTitle(db: AsyncSession, sessionId: String, title: String, userId: int) -> Result<ChatSessionResponse, Error>
        function deleteSession(db: AsyncSession, sessionId: String, userId: int) -> Result<Void, Error>
    }
    
    // Message Manager
    service MessageManager {
        function addMessage(messages: List<ChatMessage], newMessage: ChatMessage) -> List<ChatMessage]
        function generateSessionTitle(messages: List[ChatMessage]) -> String
        function formatMessagesForAI(messages: List[ChatMessage]) -> String
    }
    
    // API Router
    router ChatRouter {
        POST   /api/chat/session              -> createChatSession
        GET    /api/chat/sessions             -> getUserChatSessions
        GET    /api/chat/session/{sessionId}  -> getChatSession
        POST   /api/chat/message              -> addMessageToSession
        PUT    /api/chat/session/{sessionId}  -> updateSessionTitle
        DELETE /api/chat/session/{sessionId}  -> deleteSession
    }
    
    // WebSocket Router
    router WebSocketRouter {
        WS     /ws/chat/{sessionId}           -> handleChatWebSocket
    }
    
    // Types
    type ConversationModel {
        id: int
        userId: int
        sessionId: String
        title: String?
        messages: List[ChatMessage]  // JSON field
        createdAt: DateTime
        updatedAt: DateTime
        user: UserModel
    }
    
    type ChatMessage {
        role: String  // "user" | "assistant" | "system"
        content: String
        timestamp: DateTime
    }
    
    type ChatSessionCreate {
        title: String?
        initialMessage: String?
    }
    
    type ChatMessageCreate {
        sessionId: String
        role: String
        content: String
    }
    
    type ChatSessionResponse {
        sessionId: String
        title: String?
        messages: List[ChatMessage]
        createdAt: DateTime
        updatedAt: DateTime
    }
}

module DataCollector {
    
    // Scraping Services
    service EventsScraper {
        function scrapeEvents() -> List<EventSchema>
        function scrapeEventDetails(eventUrl: String) -> EventSchema
    }
    
    service FightersScraper {
        function scrapeFighters() -> List<FighterSchema>
        function scrapeFighterDetails(fighterUrl: String) -> FighterSchema
    }
    
    service MatchDetailScraper {
        function scrapeMatchDetails(matchUrl: String) -> MatchDetails
        function scrapeMatchStats(matchUrl: String) -> MatchStats
    }
    
    service RankingScraper {
        function scrapeRankings() -> List<RankingSchema]
        function scrapeWeightClassRankings(weightClass: String) -> List[RankingSchema]
    }
    
    // Workflow Services
    service UFCStatsFlow {
        function runFullDataCollection() -> Result<CollectionReport, Error>
        function updateEventData() -> Result<EventUpdateReport, Error>
        function updateFighterData() -> Result<FighterUpdateReport, Error>
        function syncRankings() -> Result<RankingUpdateReport, Error>
    }
    
    service DataStore {
        function storeEvents(events: List<EventSchema>) -> Result<StorageReport, Error>
        function storeFighters(fighters: List<FighterSchema]) -> Result<StorageReport, Error>
        function storeMatches(matches: List<MatchSchema]) -> Result<StorageReport, Error>
    }
    
    // Driver Management
    service Driver {
        function createWebDriver() -> WebDriver
        function closeWebDriver(driver: WebDriver) -> Void
        function configureStealth(driver: WebDriver) -> Void
    }
    
    // Main Crawler
    service Crawler {
        function crawlUFCStats() -> Result<CrawlReport, Error>
        function crawlSpecificEvent(eventId: String) -> Result<EventCrawlReport, Error>
        function crawlFighterProfile(fighterId: String) -> Result<FighterCrawlReport, Error>
    }
}

module LLM {
    
    // Provider Services
    service AnthropicProvider {
        function generateResponse(prompt: String, config: ModelConfig) -> Result<String, Error>
        function streamResponse(prompt: String, config: ModelConfig) -> AsyncIterator<String>
    }
    
    service OpenAIProvider {
        function generateResponse(prompt: String, config: ModelConfig) -> Result<String, Error>
        function streamResponse(prompt: String, config: ModelConfig) -> AsyncIterator<String>
    }
    
    service HuggingFaceProvider {
        function generateResponse(prompt: String, config: ModelConfig) -> Result<String, Error>
        function streamResponse(prompt: String, config: ModelConfig) -> AsyncIterator<String>
    }
    
    service OpenRouterProvider {
        function generateResponse(prompt: String, config: ModelConfig) -> Result<String, Error>
        function streamResponse(prompt: String, config: ModelConfig) -> AsyncIterator<String>
    }
    
    // Model Factory
    service ModelFactory {
        function createProvider(providerType: String) -> LLMProvider
        function getAvailableModels(provider: String) -> List<ModelInfo>
        function validateConfig(config: ModelConfig) -> Result<Void, Error>
    }
    
    // LangChain Service
    service LangChainService {
        function createConversationChain(provider: LLMProvider) -> ConversationChain
        function processUserMessage(chain: ConversationChain, message: String) -> Result<String, Error>
        function addMemory(chain: ConversationChain, messages: List<ChatMessage]) -> ConversationChain
    }
    
    // Agent Manager
    service AgentManager {
        function createMMAAgent() -> MMAAgent
        function processQuery(agent: MMAAgent, query: String, context: MMAContext) -> Result<AgentResponse, Error>
        function updateAgentContext(agent: MMAAgent, newData: Dict[String, Any]) -> MMAAgent
    }
    
    // Performance Monitor
    service PerformanceMonitor {
        function trackTokenUsage(provider: String, tokens: int) -> Void
        function trackResponseTime(provider: String, duration: Duration) -> Void
        function generateUsageReport() -> UsageReport
    }
    
    // Types
    type ModelConfig {
        modelName: String
        temperature: Float
        maxTokens: int
        topP: Float
        provider: String
    }
    
    type LLMProvider {
        name: String
        apiKey: String
        baseUrl: String?
        supportedModels: List<String>
    }
    
    type MMAContext {
        fighterData: List<FighterModel]
        eventData: List<EventModel]
        matchData: List<MatchModel]
        userPreferences: Dict[String, Any]
    }
}

module WebAPI {
    
    // Main Application Router
    router MainRouter {
        // Authentication
        include AuthRouter -> /api/auth
        
        // User Management  
        include UserRouter -> /api/users
        
        // Chat & Conversation
        include ChatRouter -> /api/chat
        include WebSocketRouter -> /ws
        
        // Health & Status
        GET /health -> healthCheck
        GET / -> rootEndpoint
    }
    
    // Main FastAPI Application
    app FastAPIApp {
        title: "MMA Savant API"
        description: "종합격투기(MMA) 전문 AI 어시스턴트 백엔드 API"
        version: "1.0.0"
        
        middleware: [
            CORSMiddleware,
            AuthenticationMiddleware
        ]
        
        dependencies: [
            get_async_db,
            get_current_user
        ]
        
        lifespan: applicationLifespan
    }
    
    // WebSocket Manager
    service WebSocketManager {
        function connect(websocket: WebSocket, sessionId: String) -> Void
        function disconnect(websocket: WebSocket) -> Void
        function sendMessage(sessionId: String, message: String) -> Void
        function broadcastToSession(sessionId: String, message: String) -> Void
    }
}
```

## 4. FastAPI 애플리케이션 구조 (도메인별 수직 구조)

```dsl
application FastAPIApp {
    
    main: "main_api.py"
    
    dependencies: [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "asyncpg",         // PostgreSQL async driver
        "redis",           // Redis client
        "pydantic",
        "python-jose",     // JWT handling
        "python-multipart",
        "websockets",
        "anthropic",       // Anthropic AI
        "openai",          // OpenAI
        "langchain",       // LangChain framework
        "requests",        // HTTP requests
        "beautifulsoup4",  // Web scraping
        "selenium",        // Web automation
        "pandas",          // Data processing
        "pytest",          // Testing framework
        "pytest-asyncio"   // Async testing
    ]
    
    structure {
        /
        ├── main_api.py                # FastAPI 앱 메인 엔트리포인트
        ├── config.py                  # 설정 관리 (환경변수, 키 관리)
        ├── common/                    # 공통 유틸리티
        │   ├── __init__.py
        │   ├── base_model.py         # SQLAlchemy/Pydantic 베이스
        │   ├── enums.py              # 공통 열거형
        │   ├── utils.py              # 유틸리티 함수
        │   ├── logging_config.py     # 로깅 설정
        │   └── models.py             # 공통 모델
        ├── database/                  # 데이터베이스 연결 관리
        │   ├── __init__.py
        │   ├── init_tables.py        # 테이블 초기화
        │   └── connection/
        │       ├── __init__.py
        │       ├── postgres_conn.py  # PostgreSQL 연결
        │       ├── redis_conn.py     # Redis 연결
        │       └── test_postgres_conn.py
        ├── user/                      # 사용자 도메인
        │   ├── __init__.py
        │   ├── models.py             # User 모델 및 스키마
        │   ├── services.py           # 사용자 비즈니스 로직
        │   └── exceptions.py         # 사용자 관련 예외
        ├── conversation/              # 대화 도메인
        │   ├── __init__.py
        │   ├── models.py             # Conversation 모델
        │   ├── services.py           # 채팅 세션 서비스
        │   ├── message_manager.py    # 메시지 관리
        │   └── repositories.py       # 대화 데이터 접근
        ├── fighter/                   # 파이터 도메인
        │   ├── __init__.py
        │   ├── models.py             # Fighter, Ranking 모델
        │   ├── dto.py                # 데이터 전송 객체
        │   ├── services.py           # 파이터 비즈니스 로직
        │   ├── repositories.py       # 파이터 데이터 접근
        │   └── exceptions.py         # 파이터 관련 예외
        ├── match/                     # 경기 도메인
        │   ├── __init__.py
        │   ├── models.py             # Match, FighterMatch, Stats 모델
        │   ├── dto.py                # 데이터 전송 객체
        │   ├── services.py           # 경기 비즈니스 로직
        │   ├── repositories.py       # 경기 데이터 접근
        │   └── exceptions.py         # 경기 관련 예외
        ├── event/                     # 이벤트 도메인
        │   ├── __init__.py
        │   ├── models.py             # Event 모델
        │   ├── dto.py                # 데이터 전송 객체
        │   ├── services.py           # 이벤트 비즈니스 로직
        │   ├── repositories.py       # 이벤트 데이터 접근
        │   └── exceptions.py         # 이벤트 관련 예외
        ├── api/                       # API 계층
        │   ├── __init__.py
        │   ├── main.py               # API 라우터 통합
        │   ├── auth/                 # 인증 API
        │   │   ├── __init__.py
        │   │   ├── routes.py         # 인증 엔드포인트
        │   │   ├── jwt_handler.py    # JWT 처리
        │   │   └── dependencies.py   # 인증 의존성
        │   ├── user/                 # 사용자 API
        │   │   ├── __init__.py
        │   │   └── routes.py         # 사용자 엔드포인트
        │   ├── chat/                 # 채팅 API
        │   │   ├── __init__.py
        │   │   └── routes.py         # 채팅 엔드포인트
        │   └── websocket/            # WebSocket API
        │       ├── __init__.py
        │       ├── routes.py         # WebSocket 엔드포인트
        │       └── manager.py        # WebSocket 연결 관리
        ├── data_collector/            # 데이터 수집 모듈
        │   ├── __init__.py
        │   ├── main.py               # 수집 메인 스크립트
        │   ├── crawler.py            # 메인 크롤러
        │   ├── driver.py             # WebDriver 관리
        │   ├── scrapers/             # 스크래퍼들
        │   │   ├── __init__.py
        │   │   ├── events_scraper.py
        │   │   ├── fighters_scraper.py
        │   │   ├── match_detail_scraper.py
        │   │   ├── event_detail_scraper.py
        │   │   └── ranking_scraper.py
        │   └── workflows/            # 워크플로우
        │       ├── __init__.py
        │       ├── tasks.py          # 수집 작업
        │       ├── data_store.py     # 데이터 저장
        │       ├── ufc_stats_flow.py # UFC 통계 플로우
        │       └── tests/
        │           └── test_ufc_stats_flow.py
        ├── llm/                       # LLM 통합 모듈
        │   ├── __init__.py
        │   ├── model_factory.py      # 모델 팩토리
        │   ├── langchain_service.py  # LangChain 서비스
        │   ├── agent_manager.py      # AI 에이전트 관리
        │   ├── performance_monitor.py # 성능 모니터링
        │   ├── stream_processor.py   # 스트리밍 처리
        │   ├── chart_loader.py       # 차트 로더
        │   ├── providers/            # LLM 프로바이더들
        │   │   ├── __init__.py
        │   │   ├── anthropic_provider.py
        │   │   ├── openai_provider.py
        │   │   ├── huggingface_provider.py
        │   │   └── openrouter_provider.py
        │   ├── callbacks/            # 콜백 핸들러
        │   │   ├── __init__.py
        │   │   ├── anthropic_callback.py
        │   │   ├── huggingface_callback.py
        │   │   └── openrouter_callback.py
        │   └── prompts/              # 프롬프트 템플릿
        │       ├── __init__.py
        │       ├── kr_ver.py         # 한국어 프롬프트
        │       ├── en_ver.py         # 영어 프롬프트
        │       ├── agent_prompt_templates.py
        │       └── two_phase_prompts.py
        ├── composition/               # 도메인 간 조정
        │   ├── __init__.py
        │   ├── dto.py                # 복합 DTO
        │   ├── repositories.py       # 복합 리포지토리
        │   ├── exceptions.py         # 복합 예외
        │   ├── event_composer.py     # 이벤트 컴포저
        │   ├── fighter_composer.py   # 파이터 컴포저
        │   └── match_composer.py     # 매치 컴포저
        ├── exceptions/                # 예외 정의
        │   ├── __init__.py
        │   ├── base_exception.py     # 기본 예외
        │   ├── event_exception.py    # 이벤트 예외
        │   ├── fighter_exception.py  # 파이터 예외
        │   └── match_exception.py    # 매치 예외
        ├── tests/                     # 테스트
        │   ├── __init__.py
        │   ├── conftest.py           # pytest 설정
        │   ├── composer/             # 컴포저 테스트
        │   ├── event/                # 이벤트 테스트
        │   ├── fighter/              # 파이터 테스트
        │   ├── match/                # 매치 테스트
        │   └── user/                 # 사용자 테스트
        └── tools/                     # 도구 및 스크립트
            ├── __init__.py
            └── database_tools.py     # 데이터베이스 도구
    }
    
    startup {
        loadEnvironmentVariables()
        initializeDatabase()
        setupRedisConnection()
        registerDomainRouters()
        setupCORSMiddleware()
        setupAuthenticationMiddleware()
        initializeWebSocketManager()
    }
}
```

## 5. 주요 워크플로우

```dsl
workflow UserAuthentication {
    1. POST /api/auth/login (JWT 토큰 with NextAuth.js)
    2. JWTHandler.decodeToken() -> 토큰 검증
    3. UserService.getUserByEmail() -> 사용자 조회
    4. 성공 시 사용자 정보 반환, 실패 시 401 에러
}

workflow ChatSessionManagement {
    1. POST /api/chat/session -> 새 채팅 세션 생성
    2. ChatSessionService.createNewSession() -> DB에 세션 저장
    3. WS /ws/chat/{sessionId} -> WebSocket 연결
    4. POST /api/chat/message -> 메시지 추가
    5. LLM 프로바이더를 통한 AI 응답 생성
    6. WebSocket으로 실시간 응답 스트리밍
}

workflow DataCollection {
    1. DataCollector.crawlUFCStats() 실행
    2. EventsScraper.scrapeEvents() -> 이벤트 수집
    3. FightersScraper.scrapeFighters() -> 파이터 수집
    4. MatchDetailScraper.scrapeMatchDetails() -> 경기 상세 수집
    5. DataStore.storeEvents/Fighters/Matches() -> DB 저장
    6. 결과 보고서 생성
}

workflow AIConversation {
    1. 사용자가 WebSocket으로 메시지 전송
    2. MessageManager.addMessage() -> 메시지 히스토리 관리
    3. AgentManager.processQuery() -> MMA 컨텍스트와 함께 쿼리 처리
    4. LLMProvider.streamResponse() -> AI 응답 스트리밍
    5. WebSocket으로 실시간 응답 전송
    6. ConversationRepository.updateMessages() -> DB 업데이트
}

workflow DataAnalysis {
    1. FighterService.getFighterStats() -> 파이터 통계 조회
    2. MatchService.getDetailedMatchStats() -> 경기 상세 통계
    3. EventService.getEventWithMatches() -> 이벤트와 경기 데이터
    4. LLM을 통한 데이터 분석 및 인사이트 생성
    5. 분석 결과를 사용자에게 반환
}
```

## 6. 보안 및 성능 고려사항

```dsl
security SecurityMeasures {
    authentication: JWT with NextAuth.js integration
    authorization: User-based access control
    dataProtection: Environment variables for API keys
    inputValidation: Pydantic schemas for all inputs
    cors: Configured for specific frontend domains
    
    concerns: [
        "JWT token logging in error handlers",
        "Database password in connection strings", 
        "Missing rate limiting",
        "Broad exception handling"
    ]
}

performance PerformanceOptimizations {
    database: AsyncPG for PostgreSQL async operations
    caching: Redis for session and data caching
    connectionPooling: SQLAlchemy async engine with pool
    streaming: WebSocket for real-time communication
    llmOptimization: Multiple provider support for load balancing
    
    bottlenecks: [
        "Fixed database connection pool sizes",
        "No LLM response caching",
        "Missing request batching for AI operations",
        "Synchronous scraping operations"
    ]
}
```

## 7. 개발 및 테스트 전략

```dsl
development DevelopmentStrategy {
    architecture: Domain-driven design with vertical slices
    testing: pytest with async support and comprehensive coverage
    deployment: FastAPI with uvicorn ASGI server
    monitoring: Logging with structured format and performance tracking
    
    moduleIndependence: [
        "Each domain is independently testable",
        "Shared dependencies only through common/",
        "Clear separation of concerns across layers",
        "Database transactions properly isolated"
    ]
    
    scalability: [
        "Horizontal scaling through stateless API design",
        "Redis for distributed caching",
        "Multiple LLM providers for load distribution",
        "Async operations throughout the stack"
    ]
}

testing TestStrategy {
    unitTests: Each domain has comprehensive unit test coverage
    integrationTests: API endpoint testing with test database
    performanceTests: Load testing for AI conversation flows
    securityTests: Authentication and authorization validation
    
    fixtures: [
        "test_db: In-memory PostgreSQL for testing",
        "sample_data: Predefined fighter and event data",
        "mock_llm: Mock LLM providers for testing",
        "test_client: FastAPI test client"
    ]
}
```

---

*MMA Savant 시스템 DSL 설계 v1.0 - FastAPI 기반 MMA 분석 AI 플랫폼*