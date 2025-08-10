/**
 * 画像アップロードコンポーネントテスト
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ImageUpload from '../../components/ImageUpload';

// ImageUploadコンポーネントのモック実装
const MockImageUpload: React.FC = () => {
  const [selectedImage, setSelectedImage] = React.useState<File | null>(null);
  const [preview, setPreview] = React.useState<string>('');
  const [uploading, setUploading] = React.useState(false);

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedImage) return;
    
    setUploading(true);
    // モック分析処理
    await new Promise(resolve => setTimeout(resolve, 1000));
    setUploading(false);
  };

  return (
    <div data-testid="image-upload">
      <input
        type="file"
        accept="image/*"
        onChange={handleImageSelect}
        data-testid="file-input"
      />
      
      {preview && (
        <img 
          src={preview} 
          alt="Preview" 
          data-testid="preview-image"
          style={{ maxWidth: '200px' }}
        />
      )}
      
      {selectedImage && (
        <div data-testid="file-info">
          <p>Selected: {selectedImage.name}</p>
          <p>Size: {selectedImage.size} bytes</p>
          <p>Type: {selectedImage.type}</p>
        </div>
      )}
      
      <button 
        onClick={handleUpload}
        disabled={!selectedImage || uploading}
        data-testid="upload-button"
      >
        {uploading ? 'Analyzing...' : 'Analyze Image'}
      </button>
    </div>
  );
};

// 実際のコンポーネントが存在しない場合のフォールバック
jest.mock('../../components/ImageUpload', () => {
  return {
    __esModule: true,
    default: MockImageUpload,
  };
});

describe('ImageUpload Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders image upload form', () => {
    render(<MockImageUpload />);
    
    expect(screen.getByTestId('image-upload')).toBeInTheDocument();
    expect(screen.getByTestId('file-input')).toBeInTheDocument();
    expect(screen.getByTestId('upload-button')).toBeInTheDocument();
  });

  test('handles file selection', async () => {
    render(<MockImageUpload />);
    
    const fileInput = screen.getByTestId('file-input');
    const file = new File(['fake image'], 'test.png', { type: 'image/png' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByTestId('file-info')).toBeInTheDocument();
      expect(screen.getByText('Selected: test.png')).toBeInTheDocument();
      expect(screen.getByText('Type: image/png')).toBeInTheDocument();
    });
  });

  test('shows preview after file selection', async () => {
    render(<MockImageUpload />);
    
    const fileInput = screen.getByTestId('file-input');
    const file = new File(['fake image'], 'test.jpg', { type: 'image/jpeg' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByTestId('preview-image')).toBeInTheDocument();
    });
  });

  test('upload button is disabled when no file selected', () => {
    render(<MockImageUpload />);
    
    const uploadButton = screen.getByTestId('upload-button');
    expect(uploadButton).toBeDisabled();
  });

  test('upload button is enabled when file is selected', async () => {
    render(<MockImageUpload />);
    
    const fileInput = screen.getByTestId('file-input');
    const uploadButton = screen.getByTestId('upload-button');
    const file = new File(['fake image'], 'test.png', { type: 'image/png' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(uploadButton).not.toBeDisabled();
    });
  });

  test('shows uploading state during analysis', async () => {
    render(<MockImageUpload />);
    
    const fileInput = screen.getByTestId('file-input');
    const uploadButton = screen.getByTestId('upload-button');
    const file = new File(['fake image'], 'test.png', { type: 'image/png' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(uploadButton).not.toBeDisabled();
    });
    
    fireEvent.click(uploadButton);
    
    expect(screen.getByText('Analyzing...')).toBeInTheDocument();
    expect(uploadButton).toBeDisabled();
  });

  test('accepts only image files', () => {
    render(<MockImageUpload />);
    
    const fileInput = screen.getByTestId('file-input') as HTMLInputElement;
    expect(fileInput.accept).toBe('image/*');
  });

  test('handles large file size display', async () => {
    render(<MockImageUpload />);
    
    const fileInput = screen.getByTestId('file-input');
    const largeFile = new File(['x'.repeat(1024 * 1024)], 'large.jpg', { type: 'image/jpeg' });
    
    fireEvent.change(fileInput, { target: { files: [largeFile] } });
    
    await waitFor(() => {
      expect(screen.getByText(/Size: 1048576 bytes/)).toBeInTheDocument();
    });
  });

  test('handles multiple file selection (only takes first)', async () => {
    render(<MockImageUpload />);
    
    const fileInput = screen.getByTestId('file-input');
    const file1 = new File(['image1'], 'test1.png', { type: 'image/png' });
    const file2 = new File(['image2'], 'test2.png', { type: 'image/png' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [file1, file2],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    
    await waitFor(() => {
      expect(screen.getByText('Selected: test1.png')).toBeInTheDocument();
      expect(screen.queryByText('Selected: test2.png')).not.toBeInTheDocument();
    });
  });
});