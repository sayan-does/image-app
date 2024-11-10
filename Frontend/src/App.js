import React, { useState } from 'react';
import { Loader2 } from 'lucide-react';
import './ImageProcessor.css';

const ImageProcessor = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [theme, setTheme] = useState('default');
  const [option, setOption] = useState('generate');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const themes = {
    default: 'Default Style',
    anime: 'Anime Style',
    watercolor: 'Watercolor',
    sketch: 'Pencil Sketch',
    oil_painting: 'Oil Painting',
    pixelart: 'Pixel Art',
    modern: 'Modern Art'
  };

  const options = {
    generate: 'Generate New Image',
    upscale: 'Upscale Image',
    modify: 'Modify Image'
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const formData = new FormData();
    formData.append('file', selectedImage);
    formData.append('prompt', prompt);
    formData.append('theme', theme);
    formData.append('option', option);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const arrayBuffer = await response.arrayBuffer();
      const base64 = btoa(
        new Uint8Array(arrayBuffer).reduce(
          (data, byte) => data + String.fromCharCode(byte),
          ''
        )
      );
      setProcessedImage(`data:image/jpeg;base64,${base64}`);
    } catch (error) {
      setError(error.message || 'An error occurred while processing the image');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="processor-card">
        <h1 className="title">AI Image Processor</h1>

        <div className="grid-container">
          {/* Form Section */}
          <div className="form-section">
            <form onSubmit={handleFormSubmit}>
              {/* File Upload */}
              <div className="input-group">
                <label>Upload Image</label>
                <input
                  type="file"
                  onChange={handleImageChange}
                  accept="image/*"
                />
              </div>

              {/* Prompt Input */}
              <div className="input-group">
                <label>Prompt</label>
                <input
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe your desired image..."
                />
              </div>

              {/* Theme Selection */}
              <div className="input-group">
                <label>Theme</label>
                <select
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                >
                  {Object.entries(themes).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Operation Selection */}
              <div className="input-group">
                <label>Operation</label>
                <select
                  value={option}
                  onChange={(e) => setOption(e.target.value)}
                >
                  {Object.entries(options).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading || (!selectedImage && option !== 'generate')}
                className={`submit-button ${loading ? 'loading' : ''}`}
              >
                {loading ? (
                  <>
                    <Loader2 className="spinner" size={20} />
                    Processing...
                  </>
                ) : (
                  'Process Image'
                )}
              </button>
            </form>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </div>

          {/* Preview Section */}
          <div className="preview-section">
            {/* Original Image Preview */}
            {imagePreview && (
              <div className="preview-container">
                <h3>Original Image</h3>
                <div className="image-container">
                  <img
                    src={imagePreview}
                    alt="Preview"
                  />
                </div>
              </div>
            )}

            {/* Processed Image */}
            {processedImage && (
              <div className="preview-container">
                <h3>Processed Image</h3>
                <div className="image-container">
                  <img
                    src={processedImage}
                    alt="Processed"
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageProcessor;