package com.moneyops.documents.service;

import com.moneyops.documents.entity.MoneyOpsDocument;
import com.moneyops.documents.repository.DocumentRepository;
import com.moneyops.shared.dto.PageResponse;
import com.moneyops.shared.exceptions.NotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;

import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import com.lowagie.text.pdf.PdfReader;
import com.lowagie.text.pdf.parser.PdfTextExtractor;

@Service
@RequiredArgsConstructor
public class DocumentService {

    private final DocumentRepository documentRepository;
    private static final Path UPLOAD_ROOT = Paths.get("uploads", "documents");

    public List<MoneyOpsDocument> getDocumentsByOrg(String orgId) {
        return documentRepository.findByOrgIdAndDeletedAtIsNull(orgId);
    }

    public List<MoneyOpsDocument> getVisibleDocuments(String orgId, String userId, boolean showPrivate) {
        if (showPrivate) {
            return documentRepository.findByOrgIdAndUploadedByAndIsConfidentialAndDeletedAtIsNull(orgId, userId, true);
        } else {
            return documentRepository.findByOrgIdAndIsConfidentialAndDeletedAtIsNull(orgId, false);
        }
    }

    public MoneyOpsDocument getDocumentById(String id) {
        return documentRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Document not found with ID: " + id));
    }

    public Resource loadDocumentResource(String id) {
        MoneyOpsDocument document = getDocumentById(id);
        try {
            Path path = Paths.get(document.getFirebasePath()).normalize();
            return new UrlResource(path.toUri());
        } catch (MalformedURLException e) {
            throw new IllegalStateException("Unable to load document resource", e);
        }
    }

    @Transactional
    public MoneyOpsDocument createDocumentMetadata(MoneyOpsDocument document) {
        if (document.getId() == null) {
            document.setId(UUID.randomUUID().toString());
        }
        if (document.getCreatedAt() == null) {
            document.setCreatedAt(LocalDateTime.now());
        }
        return documentRepository.save(document);
    }

    @Transactional
    public MoneyOpsDocument uploadDocument(
            MultipartFile file,
            String orgId,
            String userId,
            boolean isConfidential,
            String businessId
    ) throws IOException {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("File is required");
        }

        Files.createDirectories(UPLOAD_ROOT.resolve(orgId));

        String originalName = file.getOriginalFilename() != null ? file.getOriginalFilename() : "document";
        String safeName = originalName.replaceAll("[^a-zA-Z0-9._-]", "_");
        String storedName = UUID.randomUUID() + "_" + safeName;
        Path target = UPLOAD_ROOT.resolve(orgId).resolve(storedName);
        Files.copy(file.getInputStream(), target, StandardCopyOption.REPLACE_EXISTING);

        String extractedText = extractText(file, target);
        MoneyOpsDocument document = new MoneyOpsDocument();
        document.setId(UUID.randomUUID().toString());
        document.setOrgId(orgId);
        document.setName(originalName);
        document.setType(resolveCategory(originalName, file.getContentType()));
        document.setSize(file.getSize());
        document.setMimeType(file.getContentType());
        document.setFirebasePath(target.toAbsolutePath().toString());
        document.setDownloadUrl("/api/documents/" + document.getId() + "/download");
        document.setUploadedBy(userId);
        document.setConfidential(isConfidential);
        document.setCategory(resolveCategory(originalName, file.getContentType()));
        if (businessId != null && !businessId.isBlank()) {
            document.setLinkedEntityType("BUSINESS");
            document.setLinkedEntityId(businessId);
        }
        document.setExtractedText(extractedText);
        document.setContentSummary(buildSummary(originalName, extractedText));
        document.setDetectedDeadlines(new ArrayList<>());
        document.setCreatedAt(LocalDateTime.now());
        document.setUpdatedAt(LocalDateTime.now());

        return documentRepository.save(document);
    }

    public List<MoneyOpsDocument> getDocumentsByEntity(String entityType, String entityId) {
        return documentRepository.findByLinkedEntityTypeAndLinkedEntityIdAndDeletedAtIsNull(entityType, entityId);
    }

    @Transactional
    public void deleteDocument(String id) {
        MoneyOpsDocument document = documentRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Document not found with ID: " + id));
        
        document.setDeletedAt(LocalDateTime.now());
        document.setUpdatedAt(LocalDateTime.now());
        documentRepository.save(document);
    }

    private String resolveCategory(String fileName, String contentType) {
        String lower = fileName.toLowerCase();
        if (lower.endsWith(".pdf")) return "PDF";
        if (lower.endsWith(".txt") || lower.endsWith(".md")) return "TEXT";
        if (lower.endsWith(".csv")) return "DATA";
        if (lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png")) return "IMAGE";
        if (contentType != null && contentType.contains("word")) return "DOCUMENT";
        return "FILE";
    }

    private String buildSummary(String fileName, String extractedText) {
        if (extractedText == null || extractedText.isBlank()) {
            return "Uploaded document: " + fileName;
        }
        String compact = extractedText.replaceAll("\\s+", " ").trim();
        return compact.length() > 220 ? compact.substring(0, 220) + "..." : compact;
    }

    private String extractText(MultipartFile file, Path storedPath) throws IOException {
        String name = file.getOriginalFilename() != null ? file.getOriginalFilename().toLowerCase() : "";

        if (name.endsWith(".txt") || name.endsWith(".md") || name.endsWith(".csv") || name.endsWith(".json")) {
            return Files.readString(storedPath, StandardCharsets.UTF_8);
        }

        if (name.endsWith(".pdf")) {
            try {
                PdfReader reader = new PdfReader(storedPath.toString());
                StringBuilder builder = new StringBuilder();
                PdfTextExtractor extractor = new PdfTextExtractor(reader);
                for (int i = 1; i <= reader.getNumberOfPages(); i++) {
                    builder.append(extractor.getTextFromPage(i)).append('\n');
                }
                reader.close();
                return builder.toString().trim();
            } catch (Exception e) {
                return "";
            }
        }

        return "";
    }
}
