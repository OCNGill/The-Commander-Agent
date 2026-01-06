"""
Gillsystems Recruiter Agent - Storage Integration Example

This example demonstrates how to use the RecruiterAgentStorage
in the Recruiter Agent implementation.
"""

import asyncio
from pathlib import Path
from commander_os.agents.recruiter.recruiter_storage import RecruiterAgentStorage


async def main():
    """Example usage of RecruiterAgentStorage"""
    
    # Initialize storage
    storage = RecruiterAgentStorage(
        data_dir=Path("./data/agents/recruiter"),
        htpc_url="http://10.0.0.42:8001",  # HTPC relay URL
        enable_htpc=True
    )
    
    print("=== Recruiter Agent Storage Integration Example ===\n")
    
    # 1. Add a job requisition
    print("1. Adding job requisition...")
    job_id = await storage.add_job_requisition({
        'title': 'Senior Python Developer',
        'department': 'Engineering',
        'required_skills': ['Python', 'Django', 'PostgreSQL', 'Redis'],
        'preferred_skills': ['Docker', 'Kubernetes', 'AWS'],
        'experience_required': 5,
        'location': 'Seattle, WA',
        'priority': 8,
        'description': 'Looking for an experienced Python developer...'
    })
    print(f"   Created job: {job_id}\n")
    
    # 2. Add candidates
    print("2. Adding candidates...")
    
    candidate1_id = await storage.add_candidate({
        'name': 'Alice Johnson',
        'email': 'alice.johnson@example.com',
        'phone': '+1-555-0101',
        'skills': ['Python', 'Django', 'PostgreSQL', 'Docker'],
        'experience_years': 6,
        'education': 'BS Computer Science',
        'location': 'Seattle, WA',
        'source': 'LinkedIn'
    })
    print(f"   Added candidate: Alice Johnson ({candidate1_id})")
    
    candidate2_id = await storage.add_candidate({
        'name': 'Bob Smith',
        'email': 'bob.smith@example.com',
        'phone': '+1-555-0102',
        'skills': ['Python', 'Flask', 'MongoDB', 'React'],
        'experience_years': 4,
        'education': 'BS Software Engineering',
        'location': 'Portland, OR',
        'source': 'Referral'
    })
    print(f"   Added candidate: Bob Smith ({candidate2_id})")
    
    candidate3_id = await storage.add_candidate({
        'name': 'Charlie Davis',
        'email': 'charlie.davis@example.com',
        'phone': '+1-555-0103',
        'skills': ['Python', 'Django', 'PostgreSQL', 'Redis', 'AWS'],
        'experience_years': 8,
        'education': 'MS Computer Science',
        'location': 'San Francisco, CA',
        'source': 'Indeed'
    })
    print(f"   Added candidate: Charlie Davis ({candidate3_id})\n")
    
    # 3. Search for candidates matching the job
    print("3. Searching for candidates with required skills...")
    matches = await storage.search_candidates(
        skills=['Python', 'Django'],
        min_experience=5
    )
    
    print(f"   Found {len(matches)} matching candidates:")
    for match in matches:
        print(f"   - {match['name']}: {match['experience_years']} years, Skills: {', '.join(match['skills'])}")
    print()
    
    # 4. Schedule interviews
    print("4. Scheduling interviews...")
    
    interview1_id = await storage.add_interview({
        'candidate_id': candidate1_id,
        'interviewer_agent': 'technical-interviewer-agent',
        'scheduled_date': '2026-01-15 14:00:00',
        'interview_type': 'technical',
        'notes': 'Initial technical screening',
        'outcome': 'pending'
    })
    print(f"   Scheduled interview for Alice: {interview1_id}")
    
    interview2_id = await storage.add_interview({
        'candidate_id': candidate3_id,
        'interviewer_agent': 'technical-interviewer-agent',
        'scheduled_date': '2026-01-15 15:00:00',
        'interview_type': 'technical',
        'notes': 'Initial technical screening',
        'outcome': 'pending'
    })
    print(f"   Scheduled interview for Charlie: {interview2_id}\n")
    
    # 5. Log agent interactions
    print("5. Logging agent interactions...")
    
    interaction_id = await storage.log_agent_interaction(
        target_agent='technical-interviewer-agent',
        interaction_type='recommendation',
        context={
            'candidates': [candidate1_id, candidate3_id],
            'job_id': job_id,
            'reason': 'Strong technical skill match'
        }
    )
    print(f"   Logged interaction: {interaction_id}\n")
    
    # 6. Retrieve candidate details
    print("6. Retrieving candidate details...")
    candidate = await storage.get_candidate(candidate1_id)
    if candidate:
        print(f"   Name: {candidate['name']}")
        print(f"   Email: {candidate['email']}")
        print(f"   Skills: {', '.join(candidate['skills'])}")
        print(f"   Experience: {candidate['experience_years']} years")
        print(f"   Status: {candidate['status']}\n")
    
    # 7. Get candidate interview history
    print("7. Getting interview history...")
    interviews = await storage.get_candidate_interviews(candidate1_id)
    print(f"   {candidate['name']} has {len(interviews)} interview(s):")
    for interview in interviews:
        print(f"   - Type: {interview['interview_type']}")
        print(f"     Scheduled: {interview['scheduled_date']}")
        print(f"     Outcome: {interview['outcome']}\n")
    
    # 8. List all open jobs
    print("8. Listing all open jobs...")
    open_jobs = await storage.get_open_jobs()
    print(f"   Found {len(open_jobs)} open position(s):")
    for job in open_jobs:
        print(f"   - {job['title']} (Priority: {job['priority']})")
        print(f"     Required: {', '.join(job['required_skills'])}")
        print(f"     Experience: {job['experience_required']}+ years\n")
    
    # 9. Check storage health
    print("9. Checking storage health...")
    health = storage.health_check()
    print(f"   Agent ID: {health['agent_id']}")
    print(f"   Local DB: {'✓' if health['local_db'] else '✗'}")
    print(f"   HTPC Enabled: {'✓' if health['htpc_enabled'] else '✗'}")
    print(f"   Sync Queue Size: {health['sync_queue_size']}\n")
    
    # 10. Process sync queue (if any items are pending)
    if health['sync_queue_size'] > 0:
        print("10. Processing sync queue...")
        synced = await storage.process_sync_queue()
        print(f"   Synced {synced} record(s) to HTPC\n")
    
    # Cleanup
    await storage.close()
    print("=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
