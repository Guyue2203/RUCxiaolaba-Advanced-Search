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
                    query: searchType === 'exact' ? query.split(' ') : query
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
function renderExactResults(posts) {
    const html = posts.map(post => `
        <div class="post-card position-relative">
            <h4 class="post-title" onclick="toggleComments(this)">${post.id}</h4>
            <p>${post.content.replace(/\n/g, '<br>')}</p>
            ${post.comments.length > 0 ? 
                `<div class="comment-count">${post.comments.length}条评论</div>
                <div class="comments" style="display:none;">
                    ${post.comments.map(comment => `
                        <div class="comment-item">
                            <strong>${comment.id}</strong>: ${comment.content}
                        </div>
                    `).join('')}
                </div>` : 
                '<div class="comment-count">暂无评论</div>'
            }
        </div>
    `).join('');
    document.getElementById('results').innerHTML = html;
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