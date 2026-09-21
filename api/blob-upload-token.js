// Only responsibility: mint a short-lived, scoped token so the browser can upload a video
// straight to Vercel Blob (bypassing this platform's ~4.5 MB function-payload limit). The actual
// video bytes never pass through this function - see web/templates/index.html's submit handler.
const { handleUpload } = require('@vercel/blob/client');

module.exports = async (request, response) => {
  const body = request.body;

  try {
    const jsonResponse = await handleUpload({
      body,
      request,
      onBeforeGenerateToken: async () => ({
        allowedContentTypes: ['video/mp4', 'video/quicktime', 'video/x-m4v', 'video/x-matroska', 'video/webm'],
        addRandomSuffix: true,
        maximumSizeInBytes: 2000 * 1024 * 1024, // matches config.json max_upload_mb
      }),
      onUploadCompleted: async ({ blob }) => {
        console.log('reelflow: video uploaded to blob', blob.url);
      },
    });
    return response.status(200).json(jsonResponse);
  } catch (error) {
    return response.status(400).json({ error: error.message });
  }
};
