job_description = """

At Synexus, we're helping advertisers rethink how they show up in the news ecosystem. After a successful investment round, we are now in the process of launching a new brand and product to the Ad tech market.
   

  

 Today, blunt keyword blocking causes brands to avoid entire news sites — even when the content is high\-quality, balanced, and aligned with their values. It’s like tossing out a whole basket of fruit just because one apple has a bruise.
   

  

 Our technology changes that. Instead of just scanning keywords, Synexus analyzes how topics are being discussed. This allows advertisers to safely reintroduce premium journalism into their media plans — driving better reach, performance, and efficiency without added risk.
   

  

 At Synexus, you’ll be surrounded by people who want to improve everything and support everyone around them. Our team is passionate about our mission, are experts in their fields and are collaborative problem solvers.
   

  

 We model the following behaviors across the organisation:
   

  

 Positivity \- We approach challenges with optimism, realism, and a focus on progress.
   

  

 Respect \- We create an environment where everyone feels heard, valued, and safe to contribute.
   

  

 Accountability \- We take responsibility, keep our commitments, and support each other in delivering results.
   

  

 Outcomes Focus \- We prioritise impact over process, keeping customers, employees, and shareholders at the heart of what we do.
   

  

 Synexus is seeking applicants for a Software Engineer to join our team. We are looking for someone who is curious, resourceful, impact\-driven, and adaptable.
   

  

 As a Software Engineer on our growing team, you will play a critical role in building and scaling the infrastructure that powers our data pipeline and integrations. This is a hands\-on position where you'll work closely with engineering, data science, and product teams to deliver high\-impact solutions that make our systems faster, more reliable, and easier to use. This is a unique opportunity to have outsized impact in a fast\-paced environment, helping to shape both our technology and our engineering culture as we scale.
   

  

**Key Responsibilities**
* Enhance and maintain our open web crawling system, solving edge cases such as paywalled or obfuscated content to ensure reliable and comprehensive data collection
* Build and optimize internal tools and infrastructure that empower data scientists and analysts to access and explore large\-scale data with speed and minimal friction
* Support our transition from batch to real\-time data processing, including the design and implementation of queue\-based pipelines and event\-driven architectures
* Develop and maintain data integrations with key demand\-side platform (DSP) partners, ensuring reliable and secure data delivery at scale
* Contribute to core engineering practices such as code reviews, testing, observability, and CI/CD to help grow a robust, maintainable codebase
* Work across the stack as needed, whether improving backend performance, helping with API design, or optimizing data workflows


**Essential Experience And Behaviours**
* 3\+ years of experience building and maintaining production systems
* Strong proficiency in Python, with experience writing clean, maintainable, and well\-tested code
* Experience working with AWS services (e.g., EC2, S3, Lambda, CloudWatch, ECS/Fargate), with a focus on building reliable and scalable infrastructure
* Solid understanding of relational databases, particularly PostgreSQL, and experience writing efficient queries and managing schema changes
* Familiarity with data pipelines or event\-driven architectures, including tools like message queues (e.g., SQS, Kafka, or similar)
* Strong debugging and problem\-solving skills, with the ability to navigate ambiguity and prioritize effectively
* Experience with CI/CD pipelines and version control systems, like Git, to ensure smooth development workflows
* Excellent communication and collaboration abilities, to work effectively within a small, cross\-functional team.


**Desirable Experience And Behaviours**
* Experience working as part of a remote/virtual team
* Experience building or working with web crawlers, especially at scale or in complex environments (e.g. dynamic or paywalled content)
* Exposure to data engineering or supporting analytics workflows (e.g., building internal APIs, data tooling, or orchestration systems)
* Interest in or experience with ad tech ecosystems or API integrations with external partners
* Experience using project and task management tools for agile development (e.g. Jira, Asana, etc.)
* Bachelor’s degree in Computer Science, Engineering, or a related field
* Successful experience working with team members across countries and time zones
* Comfortable working in rapid response and in on\-call rotations


 Competitive salary (Gross annual salary in the region of USD130k\-160k)
   

  

 Health, dental, and vision benefits (US\-based team only)
   

  

 Flexible working hours and remote options. Full\-time, 1\.0 FTE (37\.5 per week)
   

  

 Some national/international travel may be required on occasion.
   

  

 As a global organization, some flexibility for cross\-time zone communication to be available for limited virtual meetings outside of office hours is required.
   

  

 Professional development opportunities
   

  

 A place to be your authentic self
   

  

 We are virtual by design to access a rich diversity of skills, expertise, experiences, and perspectives. Our commitment to neutrality is unwavering – across all of our work around the globe. Our employees are central to our mission and to our impact and we know that having varied perspectives helps generate better ideas to solve the complex challenges. We celebrate diversity and are committed to creating an inclusive environment for all employees.
   

  

 We may use artificial intelligence (AI) tools to support parts of the hiring process, such as reviewing applications, analyzing resumes, or assessing responses. These tools assist our recruitment team but do not replace human judgment. Final hiring decisions are ultimately made by humans. If you would like more information about how your data is processed, please contact us.
   

  

 Actual salary with be benchmarked against the role title and your location (tending towards the average)
 """

company_description = """
 CitiusTechis a global IT services, consulting, and business solutions enterprise 100% focused on the healthcare and life sciences industry. We enable 140+ enterprises to build a human-first ecosystem that is efficient, effective, and equitable with deep domain expertise and next-gen technology. With over 8,500 healthcare technology professionals worldwide, CitiusTech powers healthcare digital innovation, business transformation, and industry-wide convergence through next-generation technologies, solutions, and products.
"""


from app.utils.ollama_utils import parse_job_description_with_ollama

result = parse_job_description_with_ollama(job_description)
print(result)

from app.utils.company_description_parser import parse_company_description

result = parse_company_description(company_description)
print(result)