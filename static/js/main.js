document.addEventListener('DOMContentLoaded', () => {
    // 搜索类型切换
    document.querySelectorAll('.search-type').forEach(card => {
        card.addEventListener('click', () => {
            // 移除所有激活状态
            document.querySelectorAll('.search-type').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            // 更新描述文字
            const desc = document.getElementById('searchDesc');
            desc.textContent = card.dataset.type === 'exact' ? 
                '精确搜索：使用空格分隔关键词进行精准匹配' : 
                '示例：帮我总结一下法学院保研情况';
        });
    });

    // 搜索按钮点击
    document.getElementById('searchBtn').addEventListener('click', performSearch);

    async function performSearch() {

        // const sortBy = document.getElementById('sortSelect').value; // 获取排序方式
        const searchType = document.querySelector('.search-type.active').dataset.type;
        const query = document.getElementById('searchInput').value;
        const resultsDiv = document.getElementById('results');
        
        resultsDiv.innerHTML = '<div class="text-center">搜索中...</div>';

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: searchType,
                    query: searchType === 'exact' ? query.split(' ') : query,
                })
            });

            const data = await response.json();

            if (data.type === 'exact') {
                renderExactResults(data.results.posts);
            } else {
                renderAIResults(data.results);
            }
        } catch (error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">搜索失败：${error.message}</div>`;
        }
    }



    function renderAIResults(markdown) {
        document.getElementById('results').innerHTML = `
            <div class="ai-results p-3 bg-light rounded">
                ${marked.parse(markdown)}
            </div>
        `;
    }
});

// 全局函数用于切换评论显示
let currentPosts = [];
let currentKeywords = [];

function highlightKeywords(text, keywords) {
    if (!keywords || keywords.length === 0) return text;
    keywords.forEach(keyword => {
        if (keyword.trim() === '') return;
        const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(escaped, 'gi');
        text = text.replace(regex, match => `<mark>${match}</mark>`);
    });
    return text;
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}



// 新增过滤和排序函数
function filterByDate() {
    const start = document.getElementById('startDate').value;
    const end = document.getElementById('endDate').value;
    
    const filtered = currentPosts.filter(post => {
        const postDate = post.post_date.replace(/-/g, '');
        const startDate = start.replace(/-/g, '');
        const endDate = end.replace(/-/g, '');
        return (!start || postDate >= startDate) && (!end || postDate <= endDate);
    });
    
    renderExactResults(filtered);
}

function sortPosts() {
    const sortBy = document.getElementById('sortSelect').value;
    const sorted = [...currentPosts];
    
    sorted.sort((a, b) => {
        if (sortBy === 'date') {
            return b.post_date.localeCompare(a.post_date);
        } else {
            const hotA = a.good_count + a.comment_count;
            const hotB = b.good_count + b.comment_count;
            return hotB - hotA;
        }
    });
    
    renderExactResults(sorted);
}

// 修改performSearch函数保存当前结果
// 在renderExactResults函数中
function renderExactResults(posts) {
    const html = `
        <div class="sort-control mb-3">
            <select id="sortSelect" class="form-select" onchange="sortPosts(this.value)">
                <option value="time">最新排序</option>
                <option value="hot">热度排序</option>
            </select>
        </div>
        ${posts.map(post => `
            <div class="post-card position-relative">
                <h4 class="post-title" onclick="toggleComments(this)">${post.id}</h4>
                <div class="post-content">${post.content}</div>
                <div class="post-time">${post.post_time}</div>
                ${post.comments.length > 0 ? 
                    `<div class="comment-count">${post.comment_count}条评论</div>
                    <div class="comments" style="display:none;">
                        ${post.comments.map(comment => `
                            <div class="comment-item">
                                <strong>${comment.id}</strong>: ${comment.content}
                                <div class="comment-time">${comment.post_time}</div>
                            </div>
                        `).join('')}
                    </div>` : 
                    '<div class="comment-count">暂无评论</div>'
                }
            </div>
        `).join('')}
    `;
    
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = html;
    
    // 存储原始数据用于重新排序
    resultsDiv.dataset.originalPosts = JSON.stringify(posts);
}

// 新增排序函数
function sortPosts(type) {
    const resultsDiv = document.getElementById('results');
    const originalPosts = JSON.parse(resultsDiv.dataset.originalPosts);
    
    const sortedPosts = [...originalPosts].sort((a, b) => {
        if (type === 'hot') {
            return b.comment_count - a.comment_count;
        } else {
            return new Date(b.post_time) - new Date(a.post_time);
        }
    });
    
    renderExactResults(sortedPosts);
}
// function renderExactResults(posts) {
//     const html = posts.map(post => `
//         <div class="post-card position-relative" onclick="toggleComments(this)">
//             <div class="post-content">${post.content}</div>
//             <div class="comment-count">${post.comments.length}条评论</div>
//             <div class="comments">
//                 ${post.comments.map(comment => `
//                     <div class="comment-item">
//                         ${comment.content}
//                     </div>
//                 `).join('')}
//             </div>
//         </div>
//     `).join('');
//     document.getElementById('results').innerHTML = html;
// }

// 修改全局函数
function toggleComments(element) {
    const commentsDiv = element.parentElement.querySelector('.comments');
    if (commentsDiv) {
        commentsDiv.style.display = commentsDiv.style.display === 'none' ? 'block' : 'none';
    }
}
// function toggleComments(element) {
//     const commentsDiv = element.querySelector('.comments');
//     commentsDiv.style.display = commentsDiv.style.display === 'none' ? 'block' : 'none';
    
//     // 添加展开/收起动画
//     if (commentsDiv.style.display === 'block') {
//         element.classList.add('active');
//     } else {
//         element.classList.remove('active');
//     }
// }
// 添加在文件末尾
function submitFeedback() {
    const feedback = document.getElementById('feedbackInput').value;
    if (!feedback.trim()) {
        alert('请输入反馈内容');
        return;
    }

    fetch('/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ feedback: feedback })
    })
    .then(response => {
        if (response.ok) {
            alert('反馈提交成功！');
            bootstrap.Modal.getInstance(document.getElementById('feedbackModal')).hide();
        } else {
            throw new Error('提交失败');
        }
    })
    .catch(error => {
        alert('提交失败，请稍后再试');
    });
}