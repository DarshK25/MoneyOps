import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/config/api.config";
import { toast } from "sonner";
import { Upload, Download, FileText } from "lucide-react";

export default function BulkUploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [type, setType] = useState("invoices");
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const endpoint = type === "invoices" ? "/api/bulk/upload/invoices" : "/api/bulk/upload/clients";
      const response = await apiClient.post(endpoint, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(response.data);
      toast.success(`Upload complete: ${response.data.successCount} succeeded`);
    } catch (error) {
      toast.error("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = async () => {
    try {
      const endpoint = type === "invoices" ? "/api/bulk/template/invoices" : "/api/bulk/template/clients";
      const response = await apiClient.get(endpoint, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${type}-template.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error("Failed to download template");
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Bulk Upload</h1>
        <Button variant="outline" onClick={() => navigate(-1)}>Back</Button>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Upload CSV File</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Button variant={type === "invoices" ? "default" : "outline"} onClick={() => setType("invoices")}>
              Invoices
            </Button>
            <Button variant={type === "clients" ? "default" : "outline"} onClick={() => setType("clients")}>
              Clients
            </Button>
          </div>

          <div className="border-2 border-dashed rounded-lg p-8 text-center">
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-sm text-gray-600 mb-2">Click to upload or drag and drop</p>
            <input type="file" accept=".csv" onChange={handleFileChange} className="hidden" id="file-upload" />
            <label htmlFor="file-upload">
              <Button variant="outline" asChild>
                <span>Choose File</span>
              </Button>
            </label>
            {file && <p className="mt-2 text-sm">{file.name}</p>}
          </div>

          <div className="flex gap-4">
            <Button onClick={handleUpload} disabled={!file || uploading}>
              {uploading ? "Uploading..." : "Upload"}
            </Button>
            <Button variant="outline" onClick={downloadTemplate}>
              <Download className="mr-2 h-4 w-4" />
              Download Template
            </Button>
          </div>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Upload Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{result.successCount}</p>
                <p className="text-sm text-gray-600">Succeeded</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{result.failureCount}</p>
                <p className="text-sm text-gray-600">Failed</p>
              </div>
            </div>
            {result.errors?.length > 0 && (
              <div className="mt-4">
                <h3 className="font-semibold mb-2">Errors:</h3>
                <ul className="text-sm text-red-600 space-y-1">
                  {result.errors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>CSV Format</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
            {type === "invoices" 
              ? `clientName,clientEmail,description,quantity,unitPrice,gstRate,dueDate,notes
"Acme Corp","billing@acme.com","Web Dev",1,50000,18,2026-06-01,"Monthly"`
              : `name,email,phone,gstin,billingAddress,city,state,paymentTerms
"Acme Corp","billing@acme.com","+91-9876543210","29AABCA1234A1Z5","123 Main St","Mumbai","Maharashtra",30`
            }
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
