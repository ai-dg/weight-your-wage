
def get_features():
	features = [
		"MainBranch",
		"Age",
		"EdLevel",
		"Employment",
		"WorkExp",
		"LearnCode",
		"LearnCodeAI",
		"YearsCode",
		"DevType",
		"OrgSize",
		"ICorPM",
		"RemoteWork",
		"Industry",
		"Country",
		"Currency",
		"CompTotal",
		"LanguageChoice",
		"LanguageHaveWorkedWith",
		"DatabaseChoice",
		"DatabaseHaveWorkedWith",
		"PlatformChoice",
		"PlatformHaveWorkedWith",
		"WebframeChoice",
		"WebframeHaveWorkedWith",
		"DevEnvsChoice",
		"DevEnvsHaveWorkedWith",
		"AIModelsChoice",
		"AISelect",
		"AIAgents",
	]

	return features



def get_features_answers(feature: str):
	match feature:
		case "LearnCode":
			return [
				"Technical documentation (is generated for/by the tool or system)",
				"Games or coding challenges",
				"Colleague or on-the-job training",
				"Videos (not associated with specific online course or certification)",
				"Online Courses or Certification (includes all media types)",
				"Books / Physical media",
				"Stack Overflow or Stack Exchange",
				"AI CodeGen tools or AI-enabled apps",
				"Blogs or podcasts",
				"School (i.e., University, College, etc)",
				"Other online resources (e.g. standard search, forum, online community)",
				"Coding Bootcamp"
				]
		
		case "LanguageHaveWorkedWith":
			return [
				"Ada",
				"Assembly",
				"Bash/Shell (all shells)",
				"C",
				"C#",
				"C++",
				"COBOL",
				"Dart",
				"Delphi",
				"Elixir",
				"Erlang",
				"F#",
				"Fortran",
				"GDScript",
				"Go",
				"Groovy",
				"HTML/CSS",
				"Java",
				"JavaScript",
				"Kotlin",
				"Lisp",
				"Lua",
				"MATLAB",
				"MicroPython",
				"OCaml",
				"Perl",
				"PHP",
				"PowerShell",
				"Prolog",
				"Python",
				"R",
				"Ruby",
				"Rust",
				"Scala",
				"SQL",
				"Swift",
				"TypeScript",
				"VBA",
				"Visual Basic (.Net)",
				"Zig",
				"Mojo",
				"Gleam"
			]
		
		case "DatabaseHaveWorkedWith":
			return [
				"BigQuery",
				"Cassandra",
				"Cloud Firestore",
				"Cosmos DB",
				"Databricks SQL",
				"Datomic",
				"DuckDB",
				"DynamoDB",
				"Elasticsearch",
				"Firebase Realtime Database",
				"H2",
				"IBM DB2",
				"InfluxDB",
				"MariaDB",
				"Microsoft Access",
				"Microsoft SQL Server",
				"MongoDB",
				"MySQL",
				"Neo4j",
				"Oracle",
				"PostgreSQL",
				"Redis",
				"Snowflake",
				"SQLite",
				"Supabase",
				"ClickHouse",
				"CockroachDB",
				"Amazon Redshift",
				"Pocketbase",
				"Valkey",
			]

		case "PlatformHaveWorkedWith":
			return [
				"Amazon Web Services (AWS)",
				"Ansible",
				"APT",
				"Bun",
				"Cargo",
				"Chocolatey",
				"Cloudflare",
				"Composer",
				"Datadog",
				"Digital Ocean",
				"Docker",
				"Firebase",
				"Google Cloud",
				"Gradle",
				"Heroku",
				"Homebrew",
				"IBM Cloud",
				"Kubernetes",
				"Make",
				"Maven (build tool)",
				"Microsoft Azure",
				"MSBuild",
				"Netlify",
				"New Relic",
				"Ninja",
				"npm",
				"NuGet",
				"Pacman",
				"Pip",
				"pnpm",
				"Podman",
				"Poetry",
				"Prometheus",
				"Railway",
				"Splunk",
				"Supabase",
				"Terraform",
				"Vercel",
				"Vite",
				"Webpack",
				"Yandex Cloud",
				"Yarn"
			]
		
		case "WebframeHaveWorkedWith":
			return [
				"Angular",
				"AngularJS",
				"ASP.NET",
				"ASP.NET Core",
				"Astro",
				"Blazor",
				"Deno",
				"Django",
				"Drupal",
				"Express",
				"FastAPI",
				"Fastify",
				"Flask",
				"jQuery",
				"Laravel",
				"NestJS",
				"Next.js",
				"Node.js",
				"Nuxt.js",
				"Phoenix",
				"React",
				"Ruby on Rails",
				"Spring Boot",
				"Svelte",
				"Symfony",
				"Vue.js",
				"WordPress",
				"Axum"
			]

		case "DevEnvsHaveWorkedWith":
			return [
				"Aider",
				"Android Studio",
				"Bolt",
				"Claude Code",
				"Cline and/or Roo Cursor",
				"Eclipse",
				"IntelliJ IDEA",
				"Jupyter Notebook/JupyterLab",
				"Lovable.dev",
				"Nano",
				"Neovim",
				"Notepad++",
				"PhpStorm",
				"PyCharm",
				"Rider",
				"RustRover",
				"Sublime Text",
				"Trae",
				"Vim",
				"Visual Studio",
				"Visual Studio Code",
				"VSCodium",
				"WebStorm",
				"Windsurf",
				"Xcode",
				"Zed"
			]

		case "EdLevel":
			return [
				"Primary/elementary school",
				"Other (please specify):",
				"Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.)",
				"Some college/university study without earning a degree",
				"Associate degree (A.A., A.S., etc.)",
				"Bachelor’s degree (B.A., B.S., B.Eng., etc.)",
				"Master’s degree (M.A., M.S., M.Eng., MBA, etc.)",
				"Professional degree (JD, MD, Ph.D, Ed.D, etc.)"
			]

		case "AISelect":
			return [
				"Yes, I use AI tools daily",
				"Yes, I use AI tools weekly",
				"Yes, I use AI tools monthly or infrequently",
				"No, but I plan to soon",
				"No, and I don't plan to"
				]
		case "MainBranch":
			return [
				"I am a developer by profession",
				"I am not primarily a developer, but I write code sometimes as part of my work/studies",
				"I used to be a developer by profession, but no longer am",
				"I am learning to code",
				"I code primarily as a hobby",
				"I work with developers or my work supports developers but am not a developer by profession",
				"None of these",
			]
		case "Age":
			return [
				"Under 18 years old",
				"18-24 years old",
				"25-34 years old",
				"35-44 years old",
				"45-54 years old",
				"55-64 years old",
				"65 years or older",
				"Prefer not to say",
			]
		case "Employment":
			return [
				"Employed",
				"Independent contractor, freelancer, or self-employed",
				"Not employed",
				"Student",
				"Retired",
				"I prefer not to say",
			]
		case "DevType":
			return [
				"Academic researcher",
				"AI/ML engineer",
				"Applied scientist",
				"Architect, software or solutions",
				"Cloud infrastructure engineer",
				"Cybersecurity or InfoSec professional",
				"Data engineer",
				"Data or business analyst",
				"Data scientist",
				"Database administrator or engineer",
				"Developer, AI apps or physical AI",
				"Developer, back-end",
				"Developer, desktop or enterprise applications",
				"Developer, embedded applications or devices",
				"Developer, front-end",
				"Developer, full-stack",
				"Developer, game or graphics",
				"Developer, mobile",
				"Developer, QA or test",
				"DevOps engineer or professional",
				"Engineering manager",
				"Financial analyst or engineer",
				"Founder, technology or otherwise",
				"Product manager",
				"Project manager",
				"Retired",
				"Senior executive (C-suite, VP, etc.)",
				"Student",
				"Support engineer or analyst",
				"System administrator",
				"UX, Research Ops or UI design professional",
				"Other (please specify):",
			]
		
		case "OrgSize":
			return [
				"Just me - I am a freelancer, sole proprietor, etc.",
				"Less than 20 employees",
				"20 to 99 employees",
				"100 to 499 employees",
				"500 to 999 employees",
				"1,000 to 4,999 employees",
				"5,000 to 9,999 employees",
				"10,000 or more employees",
				"I don’t know",
			]
		case "ICorPM":
			return [
				"Individual contributor",
				"People manager",
			]
		case "RemoteWork":
			return [
				"Remote",
				"In-person",
				"Hybrid (some remote, leans heavy to in-person)",
				"Hybrid (some in-person, leans heavy to flexibility)",
				"Your choice (very flexible, you can come in when you want or just as needed)",
			]
		case "Industry":
			return [
				"Software Development",
				"Computer Systems Design and Services",
				"Internet, Telecomm or Information Services",
				"Fintech",
				"Energy",
				"Government",
				"Banking/Financial Services",
				"Manufacturing",
				"Transportation, or Supply Chain",
				"Healthcare",
				"Retail and Consumer Services",
				"Higher Education",
				"Media & Advertising Services",
				"Insurance",
				"Other (please specify):",
			]
		case "AIAgents":
			return [
				"Yes, I use AI agents at work daily",
				"Yes, I use AI agents at work weekly",
				"Yes, I use AI agents at work monthly or infrequently",
				"No, I use AI exclusively in copilot/autocomplete mode",
				"No, but I plan to",
				"No, and I don't plan to",
			]
		case "LearnCodeAI":
			return [
				"Yes, I learned how to use AI-enabled tools required for my job or to benefit my career",
				"Yes, I learned how to use AI-enabled tools for my personal curiosity and/or hobbies",
				"No, I learned something that was not related to AI or AI enablement as required for my job or to benefit my career",
				"No, I learned something that was not related to AI or AI enablement for my personal curiosity and/or hobbies",
				"No, I didn't spend time learning in the past year",
			]
	return None