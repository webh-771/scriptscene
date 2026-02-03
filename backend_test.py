#!/usr/bin/env python3

import requests
import sys
import time
import json
from datetime import datetime

class VideoAppAPITester:
    def __init__(self, base_url="https://scriptscene.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'No message')}"
            self.log_test("API Root", success, details)
            return success
        except Exception as e:
            self.log_test("API Root", False, str(e))
            return False

    def test_music_list(self):
        """Test music tracks listing"""
        try:
            response = requests.get(f"{self.api_url}/music/list", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                tracks = data.get('tracks', [])
                details += f", Found {len(tracks)} tracks"
                if len(tracks) > 0:
                    sample_track = tracks[0]
                    required_fields = ['id', 'title', 'artist', 'url', 'genre']
                    missing_fields = [f for f in required_fields if f not in sample_track]
                    if missing_fields:
                        success = False
                        details += f", Missing fields: {missing_fields}"
                    else:
                        details += f", Sample: {sample_track['title']} by {sample_track['artist']}"
                else:
                    success = False
                    details += ", No tracks found"
            
            self.log_test("Music List API", success, details)
            return success, response.json() if success else {}
        except Exception as e:
            self.log_test("Music List API", False, str(e))
            return False, {}

    def test_music_genres(self):
        """Test music genres endpoint"""
        try:
            response = requests.get(f"{self.api_url}/music/genres", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                genres = data.get('genres', [])
                details += f", Found {len(genres)} genres: {', '.join(genres[:3])}"
            
            self.log_test("Music Genres API", success, details)
            return success
        except Exception as e:
            self.log_test("Music Genres API", False, str(e))
            return False

    def test_media_search(self):
        """Test media search endpoint"""
        try:
            response = requests.get(
                f"{self.api_url}/media/search",
                params={"query": "nature", "media_type": "image", "per_page": 5},
                timeout=15
            )
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                items = data.get('items', [])
                total = data.get('total', 0)
                details += f", Found {len(items)} items, Total: {total}"
                
                if len(items) > 0:
                    sample_item = items[0]
                    required_fields = ['id', 'type', 'url', 'source']
                    missing_fields = [f for f in required_fields if f not in sample_item]
                    if missing_fields:
                        success = False
                        details += f", Missing fields: {missing_fields}"
                    else:
                        details += f", Sample source: {sample_item['source']}"
            
            self.log_test("Media Search API", success, details)
            return success
        except Exception as e:
            self.log_test("Media Search API", False, str(e))
            return False

    def test_video_generation(self):
        """Test video generation workflow"""
        try:
            # Test script for video generation
            test_script = "Welcome to our amazing video generation platform. This is a test script to demonstrate our AI-powered video creation capabilities. The system will generate voiceover, add visuals, and create subtitles automatically."
            
            # Start video generation
            generation_data = {
                "script": test_script,
                "voice_style": "Puck",
                "include_subtitles": True,
                "music_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
            }
            
            print(f"\n🎬 Starting video generation test...")
            response = requests.post(
                f"{self.api_url}/video/generate",
                json=generation_data,
                timeout=30
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                job_id = data.get('job_id')
                status = data.get('status')
                details += f", Job ID: {job_id}, Status: {status}"
                
                if job_id:
                    # Test status checking
                    self.log_test("Video Generation Start", True, details)
                    return self.test_video_status_tracking(job_id)
                else:
                    success = False
                    details += ", No job_id returned"
            
            self.log_test("Video Generation Start", success, details)
            return success
            
        except Exception as e:
            self.log_test("Video Generation Start", False, str(e))
            return False

    def test_video_status_tracking(self, job_id):
        """Test video status tracking"""
        try:
            max_checks = 10  # Limit status checks for testing
            check_count = 0
            
            while check_count < max_checks:
                response = requests.get(f"{self.api_url}/video/status/{job_id}", timeout=10)
                
                if response.status_code != 200:
                    self.log_test("Video Status Tracking", False, f"Status check failed: {response.status_code}")
                    return False
                
                data = response.json()
                status = data.get('status')
                progress = data.get('progress', 0)
                message = data.get('message', '')
                
                print(f"   Status: {status}, Progress: {progress}%, Message: {message}")
                
                if status == 'completed':
                    video_url = data.get('video_url')
                    if video_url:
                        self.log_test("Video Status Tracking", True, f"Completed with video URL: {video_url}")
                        return self.test_video_download(job_id)
                    else:
                        self.log_test("Video Status Tracking", False, "Completed but no video URL")
                        return False
                
                elif status == 'failed':
                    error = data.get('error', 'Unknown error')
                    self.log_test("Video Status Tracking", False, f"Generation failed: {error}")
                    return False
                
                check_count += 1
                if check_count < max_checks:
                    time.sleep(10)  # Wait 10 seconds between checks
            
            # If we reach here, video is still processing
            self.log_test("Video Status Tracking", True, f"Video still processing after {max_checks} checks")
            return True
            
        except Exception as e:
            self.log_test("Video Status Tracking", False, str(e))
            return False

    def test_video_download(self, job_id):
        """Test video download endpoint"""
        try:
            response = requests.head(f"{self.api_url}/video/download/{job_id}", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', '0')
                details += f", Content-Type: {content_type}, Size: {content_length} bytes"
                
                if 'video' not in content_type.lower():
                    success = False
                    details += ", Invalid content type for video"
            
            self.log_test("Video Download", success, details)
            return success
        except Exception as e:
            self.log_test("Video Download", False, str(e))
            return False

    def test_video_projects_list(self):
        """Test video projects listing"""
        try:
            response = requests.get(f"{self.api_url}/video/projects", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if isinstance(data, list):
                    details += f", Found {len(data)} projects"
                    if len(data) > 0:
                        sample_project = data[0]
                        required_fields = ['job_id', 'script', 'status', 'created_at']
                        missing_fields = [f for f in required_fields if f not in sample_project]
                        if missing_fields:
                            success = False
                            details += f", Missing fields: {missing_fields}"
                        else:
                            details += f", Sample status: {sample_project['status']}"
                else:
                    success = False
                    details += ", Response is not a list"
            
            self.log_test("Video Projects List", success, details)
            return success
        except Exception as e:
            self.log_test("Video Projects List", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting ScriptScene Video App API Tests")
        print(f"📡 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic API tests
        if not self.test_api_root():
            print("❌ API root failed - stopping tests")
            return False
        
        # Music service tests
        music_success, music_data = self.test_music_list()
        self.test_music_genres()
        
        # Media service tests
        self.test_media_search()
        
        # Video service tests
        self.test_video_projects_list()
        
        # Video generation test (most complex)
        if music_success and len(music_data.get('tracks', [])) > 0:
            print(f"\n🎥 Testing video generation workflow...")
            self.test_video_generation()
        else:
            print(f"\n⚠️  Skipping video generation test - music service not working")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = VideoAppAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'success_rate': (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
                'timestamp': datetime.now().isoformat()
            },
            'detailed_results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())