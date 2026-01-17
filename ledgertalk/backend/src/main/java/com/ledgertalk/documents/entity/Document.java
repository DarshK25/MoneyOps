// documents/entity/Document.java
import 

@Entity
@Table(name = "documents")
@Data
public class Document {

    @Id
    @GeneratedValue
    private UUID id;

    private UUID orgId;
    private String name;
    private String type;
    private Long size;
    private String firebasePath;
    private String downloadUrl;
    private String mimeType;
    private UUID uploadedBy;
    private String linkedEntityType;
    private UUID linkedEntityId;

    private LocalDateTime createdAt;
}
