package in.aitrove.contracts;
import jakarta.persistence.*;
import java.util.UUID;
import org.hibernate.SessionFactory;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import java.util.Properties;
public class JpaContracts implements AutoCloseable {
    @Entity(name="StockAccount") @Table(name="stock_account")
    public static class StockAccount {
        @Id public Long id;
        @Version public Long version;
        public int available;
        protected StockAccount() {}
        public int getAvailable() {return available;}
        public StockAccount(long id,int available) { this.id=id; this.available=available; }
    }
    @Entity(name="StockLine") @Table(name="stock_line")
    public static class StockLine {
        @Id public Long id;
        @ManyToOne(fetch=FetchType.LAZY,optional=false) @JoinColumn(name="account_id")
        public StockAccount account;
        public int units;
        protected StockLine() {}
        public StockLine(long id,StockAccount account,int units) { this.id=id;this.account=account;this.units=units; }
    }
    public final EntityManagerFactory factory;
    public JpaContracts() {
        var builder=new LocalContainerEntityManagerFactoryBean();
        builder.setDataSource(new DriverManagerDataSource("jdbc:h2:mem:jpa_"+UUID.randomUUID()+";DB_CLOSE_DELAY=-1","sa",""));
        builder.setPackagesToScan("in.aitrove.contracts");
        builder.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties settings=new Properties();
        settings.put("hibernate.hbm2ddl.auto","create-drop");
        settings.put("hibernate.generate_statistics","true");
        builder.setJpaProperties(settings); builder.afterPropertiesSet();
        factory=builder.getObject();
    }
    public void seed() {
        try (EntityManager manager=factory.createEntityManager()) {
            manager.getTransaction().begin();
            for (long id=1;id<=3;id++) {
                StockAccount account=new StockAccount(id,100);
                manager.persist(account); manager.persist(new StockLine(id,account,10));
            }
            manager.getTransaction().commit();
        }
    }
    public org.hibernate.stat.Statistics statistics() { return factory.unwrap(SessionFactory.class).getStatistics(); }
    public void close() { factory.close(); }
}
