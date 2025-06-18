"""GitHub integration for the AI Assistant."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from github import Github, GithubException

from .base_integration import BaseIntegration, AuthenticationError, APIError

logger = logging.getLogger(__name__)

class GitHubIntegration(BaseIntegration):
    """GitHub integration for repository and PR management."""
    
    def __init__(self, cache_duration: int = 600):
        super().__init__("GitHub", cache_duration)
        self.github = None
        self.user = None
    
    async def authenticate(self) -> bool:
        """Authenticate with GitHub using personal access token."""
        try:
            from ..config import config
            token = config.github_token
            
            if not token:
                logger.error("GitHub token not configured")
                return False
            
            self.github = Github(token)
            self.user = self.github.get_user()
            
            # Test authentication by getting user info
            _ = self.user.login  # This will raise an exception if auth fails
            
            self.authenticated = True
            logger.info(f"GitHub authentication successful for user: {self.user.login}")
            return True
            
        except GithubException as e:
            logger.error(f"GitHub authentication failed: {e}")
            raise AuthenticationError(f"GitHub authentication failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during GitHub authentication: {e}")
            raise AuthenticationError(f"Unexpected error during GitHub authentication: {e}")
    
    async def test_connection(self) -> bool:
        """Test GitHub connection."""
        if not self.github or not self.user:
            return False
        
        try:
            # Try to get user info
            _ = self.user.login
            return True
        except GithubException:
            return False
    
    async def get_pull_requests(self, state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
        """Get pull requests for user's repositories."""
        cache_key = f"prs_{state}_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            prs = []
            repos = self.user.get_repos(type="owner", sort="updated")
            
            pr_count = 0
            for repo in repos:
                if pr_count >= limit:
                    break
                
                repo_prs = repo.get_pulls(state=state)
                for pr in repo_prs:
                    if pr_count >= limit:
                        break
                    
                    pr_data = {
                        'id': pr.id,
                        'number': pr.number,
                        'title': pr.title,
                        'state': pr.state,
                        'repository': repo.name,
                        'author': pr.user.login,
                        'created_at': pr.created_at.isoformat(),
                        'updated_at': pr.updated_at.isoformat(),
                        'url': pr.html_url,
                        'draft': pr.draft,
                        'mergeable': pr.mergeable,
                        'comments': pr.comments,
                        'commits': pr.commits,
                        'additions': pr.additions,
                        'deletions': pr.deletions
                    }
                    prs.append(pr_data)
                    pr_count += 1
            
            self._set_cache(cache_key, prs)
            return prs
            
        except GithubException as e:
            logger.error(f"Failed to get pull requests: {e}")
            raise APIError(f"Failed to get pull requests: {e}")
    
    async def get_issues_assigned_to_me(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get issues assigned to the authenticated user."""
        cache_key = f"my_issues_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            issues = []
            user_issues = self.github.search_issues(f"assignee:{self.user.login} is:open")
            
            for issue in user_issues[:limit]:
                issue_data = {
                    'id': issue.id,
                    'number': issue.number,
                    'title': issue.title,
                    'state': issue.state,
                    'repository': issue.repository.name,
                    'author': issue.user.login,
                    'created_at': issue.created_at.isoformat(),
                    'updated_at': issue.updated_at.isoformat(),
                    'url': issue.html_url,
                    'labels': [label.name for label in issue.labels],
                    'comments': issue.comments,
                    'body': issue.body[:200] + '...' if issue.body and len(issue.body) > 200 else issue.body
                }
                issues.append(issue_data)
            
            self._set_cache(cache_key, issues)
            return issues
            
        except GithubException as e:
            logger.error(f"Failed to get assigned issues: {e}")
            raise APIError(f"Failed to get assigned issues: {e}")
    
    async def get_recent_commits(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits by the user."""
        cache_key = f"recent_commits_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            commits = []
            repos = self.user.get_repos(type="owner", sort="updated")
            
            commit_count = 0
            for repo in repos:
                if commit_count >= limit:
                    break
                
                try:
                    repo_commits = repo.get_commits(author=self.user)
                    for commit in repo_commits:
                        if commit_count >= limit:
                            break
                        
                        commit_data = {
                            'sha': commit.sha[:8],  # Short SHA
                            'message': commit.commit.message.split('\n')[0],  # First line only
                            'repository': repo.name,
                            'date': commit.commit.author.date.isoformat(),
                            'url': commit.html_url,
                            'additions': commit.stats.additions if commit.stats else 0,
                            'deletions': commit.stats.deletions if commit.stats else 0
                        }
                        commits.append(commit_data)
                        commit_count += 1
                        
                except GithubException:
                    # Skip repositories that we can't access
                    continue
            
            # Sort by date (most recent first)
            commits.sort(key=lambda x: x['date'], reverse=True)
            
            self._set_cache(cache_key, commits)
            return commits
            
        except GithubException as e:
            logger.error(f"Failed to get recent commits: {e}")
            raise APIError(f"Failed to get recent commits: {e}")
    
    async def get_repository_stats(self) -> Dict[str, Any]:
        """Get user's repository statistics."""
        cache_key = "repo_stats"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            repos = list(self.user.get_repos(type="owner"))
            
            stats = {
                'total_repos': len(repos),
                'public_repos': sum(1 for repo in repos if not repo.private),
                'private_repos': sum(1 for repo in repos if repo.private),
                'total_stars': sum(repo.stargazers_count for repo in repos),
                'total_forks': sum(repo.forks_count for repo in repos),
                'languages': {},
                'most_starred': None,
                'most_recent': None
            }
            
            # Get language distribution
            for repo in repos:
                if repo.language:
                    stats['languages'][repo.language] = stats['languages'].get(repo.language, 0) + 1
            
            # Most starred repository
            if repos:
                most_starred = max(repos, key=lambda r: r.stargazers_count)
                stats['most_starred'] = {
                    'name': most_starred.name,
                    'stars': most_starred.stargazers_count,
                    'url': most_starred.html_url
                }
                
                # Most recently updated repository
                most_recent = max(repos, key=lambda r: r.updated_at)
                stats['most_recent'] = {
                    'name': most_recent.name,
                    'updated_at': most_recent.updated_at.isoformat(),
                    'url': most_recent.html_url
                }
            
            self._set_cache(cache_key, stats)
            return stats
            
        except GithubException as e:
            logger.error(f"Failed to get repository stats: {e}")
            raise APIError(f"Failed to get repository stats: {e}")
    
    async def get_prs_to_review(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pull requests that need review from the user."""
        cache_key = f"prs_to_review_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Search for PRs where user is requested as reviewer
            search_query = f"is:pr is:open review-requested:{self.user.login}"
            prs = []
            
            pr_issues = self.github.search_issues(search_query)
            
            for issue in pr_issues[:limit]:
                # Get the actual PR object for more details
                repo = self.github.get_repo(issue.repository.full_name)
                pr = repo.get_pull(issue.number)
                
                pr_data = {
                    'id': pr.id,
                    'number': pr.number,
                    'title': pr.title,
                    'repository': repo.name,
                    'author': pr.user.login,
                    'created_at': pr.created_at.isoformat(),
                    'updated_at': pr.updated_at.isoformat(),
                    'url': pr.html_url,
                    'draft': pr.draft,
                    'commits': pr.commits,
                    'additions': pr.additions,
                    'deletions': pr.deletions
                }
                prs.append(pr_data)
            
            self._set_cache(cache_key, prs)
            return prs
            
        except GithubException as e:
            logger.error(f"Failed to get PRs to review: {e}")
            raise APIError(f"Failed to get PRs to review: {e}") 